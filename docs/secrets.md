# GitHub Secrets

Required secrets for ServerPulse CI/CD workflows.

## Deploy Workflow (`deploy.yml`)

| Secret | Description | Example |
|--------|-------------|---------|
| `GHCR_TOKEN` | GitHub PAT with `write:packages` scope for pushing to GHCR | `ghp_xxxxxxxxxxxxxxxxxxxx` |
| `DEPLOY_HOST` | VPS hostname or IP address | `192.168.1.100` |
| `DEPLOY_USER` | SSH user on the VPS | `deploy` |
| `DEPLOY_KEY` | SSH private key for passwordless deploy access | `-----BEGIN OPENSSH PRIVATE KEY-----...` |

## CI Workflow (`ci.yml`)

No secrets required. CI uses hardcoded test values for `JWT_SECRET` and `AGENT_TOKEN_SALT`.

## Setup

1. Go to **Settings > Secrets and variables > Actions** in your GitHub repository
2. Add each secret listed above
3. For `DEPLOY_KEY`, generate an SSH key pair:
   ```bash
   ssh-keygen -t ed25519 -C "serverpulse-deploy" -f ~/.ssh/serverpulse_deploy
   ```
4. Add the public key to the VPS `authorized_keys` for the deploy user
5. Add the private key as the `DEPLOY_KEY` secret

## Security Notes

- Rotate `GHCR_TOKEN` periodically
- Use a dedicated deploy user with minimal permissions on the VPS
- Never commit secrets or `.env` files to the repository
