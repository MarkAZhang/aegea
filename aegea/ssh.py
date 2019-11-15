"""
Connect to an EC2 instance via SSH, by name or instance ID.

Security groups, network ACLs, interfaces, VPC routing tables, VPC
Internet Gateways, and internal firewalls for the instance must be
configured to allow SSH connections.

To facilitate SSH connections, ``aegea ssh`` resolves instance names
to public DNS names assigned by AWS, and securely retrieves SSH host
public keys from instance metadata before connecting. This avoids both
the prompt to save the instance public key and the resulting transient
MITM vulnerability.

``aegea ssh`` also supports Bless, via the --bless-config CONFIG_FILE
option or the BLESS_CONFIG environment variable. This should point to a
YAML file with the format described in
https://github.com/chanzuckerberg/blessclient/blob/master/examples/config.yml.
"""

import os, sys, argparse, string, datetime, json, base64, time, fnmatch

import boto3, yaml

from . import register_parser, logger
from .util.aws import resolve_instance_id, resources, clients, ARN
from .util.crypto import (add_ssh_host_key_to_known_hosts, ensure_local_ssh_key, get_public_key_from_pair,
                          add_ssh_key_to_agent, get_ssh_key_path)
from .util.printing import BOLD
from .util.exceptions import AegeaException
from .util.compat import lru_cache

@lru_cache(8)
def get_instance(name):
    return resources.ec2.Instance(resolve_instance_id(name))

def resolve_instance_public_dns(name):
    instance = get_instance(name)
    if not getattr(instance, "public_dns_name", None):
        msg = "Unable to resolve public DNS name for {} (state: {})"
        raise AegeaException(msg.format(instance, getattr(instance, "state", {}).get("Name")))

    tags = {tag["Key"]: tag["Value"] for tag in instance.tags or []}
    ssh_host_key = tags.get("SSHHostPublicKeyPart1", "") + tags.get("SSHHostPublicKeyPart2", "")
    if ssh_host_key:
        # FIXME: this results in duplicates.
        # Use paramiko to detect if the key is already listed and not insert it then (or only insert if different)
        add_ssh_host_key_to_known_hosts(instance.public_dns_name + " " + ssh_host_key + "\n")
    return instance.public_dns_name

def get_linux_username():
    username = ARN.get_iam_username()
    assert username != "unknown"
    username, at, domain = username.partition("@")
    return username

def get_kms_auth_token(session, bless_config, lambda_regional_config):
    logger.info("Requesting new KMS auth token in %s", lambda_regional_config["aws_region"])
    token_not_before = datetime.datetime.utcnow() - datetime.timedelta(minutes=1)
    token_not_after = token_not_before + datetime.timedelta(hours=1)
    token = dict(not_before=token_not_before.strftime("%Y%m%dT%H%M%SZ"),
                 not_after=token_not_after.strftime("%Y%m%dT%H%M%SZ"))
    encryption_context = {
        "from": session.resource("iam").CurrentUser().user_name,
        "to": bless_config["lambda_config"]["function_name"],
        "user_type": "user"
    }
    kms = session.client('kms', region_name=lambda_regional_config["aws_region"])
    res = kms.encrypt(KeyId=lambda_regional_config["kms_auth_key_id"],
                      Plaintext=json.dumps(token),
                      EncryptionContext=encryption_context)
    return base64.b64encode(res["CiphertextBlob"]).decode()

def ensure_bless_ssh_cert(ssh_key_name, bless_config, use_kms_auth, max_cert_age=1800):
    ssh_key = ensure_local_ssh_key(ssh_key_name)
    ssh_key_filename = get_ssh_key_path(ssh_key_name)
    ssh_cert_filename = ssh_key_filename + "-cert.pub"
    if os.path.exists(ssh_cert_filename) and time.time() - os.stat(ssh_cert_filename).st_mtime < max_cert_age:
        logger.info("Using cached Bless SSH certificate %s", ssh_cert_filename)
        return ssh_cert_filename
    logger.info("Requesting new Bless SSH certificate")

    for lambda_regional_config in bless_config["lambda_config"]["regions"]:
        if lambda_regional_config["aws_region"] == clients.ec2.meta.region_name:
            break
    session = boto3.Session(profile_name=bless_config["client_config"]["aws_user_profile"])
    iam = session.resource("iam")
    sts = session.client("sts")
    assume_role_res = sts.assume_role(RoleArn=bless_config["lambda_config"]["role_arn"], RoleSessionName=__name__)
    awslambda = boto3.client('lambda',
                             region_name=lambda_regional_config["aws_region"],
                             aws_access_key_id=assume_role_res['Credentials']['AccessKeyId'],
                             aws_secret_access_key=assume_role_res['Credentials']['SecretAccessKey'],
                             aws_session_token=assume_role_res['Credentials']['SessionToken'])
    bless_input = dict(bastion_user=iam.CurrentUser().user_name,
                       bastion_user_ip="0.0.0.0/0",
                       bastion_ips=",".join(bless_config["client_config"]["bastion_ips"]),
                       remote_usernames=",".join(bless_config["client_config"]["remote_users"]),
                       public_key_to_sign=get_public_key_from_pair(ssh_key),
                       command="*")
    if use_kms_auth:
        bless_input["kmsauth_token"] = get_kms_auth_token(session=session,
                                                          bless_config=bless_config,
                                                          lambda_regional_config=lambda_regional_config)
    res = awslambda.invoke(FunctionName=bless_config["lambda_config"]["function_name"], Payload=json.dumps(bless_input))
    bless_output = json.loads(res["Payload"].read().decode())
    if "certificate" not in bless_output:
        raise AegeaException("Error while requesting Bless SSH certificate: {}".format(bless_output))
    with open(ssh_cert_filename, "w") as fh:
        fh.write(bless_output["certificate"])
    return ssh_cert_filename

def match_instance_to_bastion(instance, bastions):
    for bastion_config in bastions:
        for ipv4_pattern in bastion_config["hosts"]:
            if fnmatch.fnmatch(instance.private_ip_address, ipv4_pattern["pattern"]):
                logger.info("Using %s to connect to %s", bastion_config["pattern"], instance)
                return bastion_config
    raise AegeaException("Unable to determine Bless bastion config for {}".format(instance))

def prepare_ssh_opts(username, hostname, bless_config_filename=None, ssh_key_name=__name__, use_kms_auth=True):
    if bless_config_filename:
        with open(bless_config_filename) as fh:
            bless_config = yaml.safe_load(fh)
        ensure_bless_ssh_cert(ssh_key_name=ssh_key_name,
                              bless_config=bless_config,
                              use_kms_auth=use_kms_auth)
        add_ssh_key_to_agent(ssh_key_name)
        instance = get_instance(hostname)
        bastion_config = match_instance_to_bastion(instance=instance, bastions=bless_config["ssh_config"]["bastions"])
        if not username:
            username = bless_config["client_config"]["remote_users"][0]
        jump_host = bastion_config["user"] + "@" + bastion_config["pattern"]
        return ["-l", username, "-J", jump_host, instance.private_ip_address]
    else:
        if get_instance(hostname).key_name is not None:
            add_ssh_key_to_agent(get_instance(hostname).key_name)
        if not username:
            username = get_linux_username()
        return ["-l", username, resolve_instance_public_dns(hostname)]

def ssh(args):
    ssh_opts = ["-o", "ServerAliveInterval={}".format(args.server_alive_interval)]
    ssh_opts += ["-o", "ServerAliveCountMax={}".format(args.server_alive_count_max)]
    for ssh_opt in ssh_opts_by_nargs[0]:
        if getattr(args, ssh_opt):
            ssh_opts.append("-" + ssh_opt)
    for ssh_opt in ssh_opts_by_nargs[1]:
        for value in getattr(args, ssh_opt) or []:
            ssh_opts.extend(["-" + ssh_opt, value])
    prefix, at, name = args.name.rpartition("@")
    ssh_opts += prepare_ssh_opts(username=prefix, hostname=name, bless_config_filename=args.bless_config)
    os.execvp("ssh", ["ssh"] + ssh_opts + args.ssh_args)

ssh_parser = register_parser(ssh, help="Connect to an EC2 instance", description=__doc__)
ssh_parser.add_argument("name")
ssh_parser.add_argument("ssh_args", nargs=argparse.REMAINDER,
                        help="Arguments to pass to ssh; please see " + BOLD("man ssh") + " for details")
ssh_parser.add_argument("--server-alive-interval", help=argparse.SUPPRESS)
ssh_parser.add_argument("--server-alive-count-max", help=argparse.SUPPRESS)
ssh_parser.add_argument("--bless-config", default=os.environ.get("BLESS_CONFIG"),
                        help="Path to a Bless configuration file (or pass via the BLESS_CONFIG environment variable)")
ssh_opts_by_nargs = {0: "46AaCfGgKkMNnqsTtVvXxYy", 1: "BbcDEeFIiJLlmOopQRSW"}
for ssh_opt in ssh_opts_by_nargs[0]:
    ssh_parser.add_argument("-" + ssh_opt, action="store_true", help=argparse.SUPPRESS)
for ssh_opt in ssh_opts_by_nargs[1]:
    ssh_parser.add_argument("-" + ssh_opt, action="append", help=argparse.SUPPRESS)

def scp(args):
    """
    Transfer files to or from EC2 instance.

    Use "--" to separate scp args from aegea args:

        aegea scp -- -r local_dir instance_name:~/remote_dir
    """
    if args.scp_args[0] == "--":
        del args.scp_args[0]
    user_or_hostname_chars = string.ascii_letters + string.digits
    for i, arg in enumerate(args.scp_args):
        if arg[0] in user_or_hostname_chars and ":" in arg:
            hostname, colon, path = arg.partition(":")
            username, at, hostname = hostname.rpartition("@")
            hostname = resolve_instance_public_dns(hostname)
            if not (username or at):
                try:
                    username, at = get_linux_username(), "@"
                except Exception:
                    logger.info("Unable to determine IAM username, using local username")
            args.scp_args[i] = username + at + hostname + colon + path
    os.execvp("scp", ["scp"] + args.scp_args)

scp_parser = register_parser(scp, help="Transfer files to or from EC2 instance", description=scp.__doc__)
scp_parser.add_argument("scp_args", nargs=argparse.REMAINDER,
                        help="Arguments to pass to scp; please see " + BOLD("man scp") + " for details")
