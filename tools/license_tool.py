"""Offline signing utility for ProjectMng licenses.

Run this tool only on the system owner's computer.  Never copy the private
key to a deployed server or commit it to Git.
"""

import argparse
import base64
import getpass
import json
import uuid
from datetime import date
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def canonical_payload(payload):
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def read_password(prompt):
    password = getpass.getpass(prompt)
    if not password:
        raise SystemExit("私钥密码不能为空。")
    return password.encode("utf-8")


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def generate_keypair(args):
    private_path = Path(args.private_key)
    public_path = Path(args.public_key)
    if (private_path.exists() or public_path.exists()) and not args.force:
        raise SystemExit("密钥文件已存在；如确实需要覆盖，请显式加 --force。")
    password = read_password("设置私钥保护密码：")
    confirmation = read_password("再次输入私钥保护密码：")
    if password != confirmation:
        raise SystemExit("两次密码不一致。")
    private_key = Ed25519PrivateKey.generate()
    private_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)
    private_path.write_bytes(private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(password),
    ))
    public_path.write_bytes(private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ))
    print(f"已生成私钥：{private_path}")
    print(f"已生成公钥：{public_path}")
    print("私钥仅由你保存；部署服务器只需要公钥。")


def issue_license(args):
    request_data = json.loads(Path(args.request).read_text(encoding="utf-8"))
    fingerprint = request_data.get("machine_fingerprint", "")
    if not fingerprint:
        raise SystemExit("授权请求文件缺少机器码。")
    expires_at = date.fromisoformat(args.expires_at)
    if expires_at <= date.today():
        raise SystemExit("到期日必须晚于今天。")
    password = read_password("输入私钥保护密码：")
    private_key = serialization.load_pem_private_key(Path(args.private_key).read_bytes(), password=password)
    payload = {
        "version": 1,
        "license_id": args.license_id or str(uuid.uuid4()),
        "customer": args.customer,
        "issued_at": date.today().isoformat(),
        "expires_at": expires_at.isoformat(),
        "machine_fingerprint": fingerprint,
    }
    signature = private_key.sign(canonical_payload(payload))
    envelope = {
        "algorithm": "Ed25519",
        "payload": payload,
        "signature": base64.b64encode(signature).decode("ascii"),
    }
    write_json(args.output, envelope)
    print(f"已签发授权文件：{args.output}")


def main():
    parser = argparse.ArgumentParser(description="交付中台离线授权签发工具")
    commands = parser.add_subparsers(dest="command", required=True)

    generate = commands.add_parser("generate-keypair", help="生成受密码保护的私钥和可部署的公钥")
    generate.add_argument("--private-key", required=True, help="私钥保存路径，仅系统所有者保留")
    generate.add_argument("--public-key", required=True, help="公钥保存路径，复制到部署服务器")
    generate.add_argument("--force", action="store_true", help="覆盖已有密钥文件")
    generate.set_defaults(handler=generate_keypair)

    issue = commands.add_parser("issue", help="根据授权请求文件签发授权")
    issue.add_argument("--request", required=True, help="服务器导出的授权请求 JSON")
    issue.add_argument("--private-key", required=True, help="系统所有者保存的私钥")
    issue.add_argument("--customer", required=True, help="授权客户名称")
    issue.add_argument("--expires-at", required=True, help="到期日期，例如 2027-02-26")
    issue.add_argument("--output", required=True, help="生成的 .lic 文件路径")
    issue.add_argument("--license-id", default="", help="可选的授权编号")
    issue.set_defaults(handler=issue_license)

    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
