# Security Policy

This repository is intended to be public. Do not commit:

- `.env` files or deployment-specific connection settings
- raw browser captures such as `*.har`
- private Compute Box network details tied to a customer/site
- credentials, cookies, tokens, or session IDs

The API can command real gripper motion and vacuum. Run examples only on
hardware you are authorized to operate, keep force/speed/vacuum conservative
while validating, and ensure the robot cell is safe before actuating a gripper.

Report suspected credential exposure or unsafe behavior privately to the
maintainers before opening a public issue.
