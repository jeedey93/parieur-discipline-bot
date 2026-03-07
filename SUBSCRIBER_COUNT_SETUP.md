# Subscriber Count Setup

The website displays a subscriber count badge in the hero section. This count is automatically calculated from the `EMAIL_TO` secret.

## How It Works

- The script reads the `EMAIL_TO` secret (which contains comma-separated email addresses)
- It counts the number of emails in the list
- Example: `email1@example.com,email2@example.com,email3@example.com` = 3 subscribers
- The count is displayed in the hero section as "X subscribers already joined"

## Technical Details

- The `EMAIL_TO` secret is already used for sending email notifications
- No additional setup required - it uses the existing secret
- The count updates automatically when you add/remove emails from `EMAIL_TO`
- Runs during both the 6am results workflow and 7am/12pm predictions workflows
- The count is embedded in the HTML as a static value

## Updating the Count

To change the subscriber count, simply update the `EMAIL_TO` secret:
1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click on `EMAIL_TO`
3. Add or remove email addresses (comma-separated)
4. Click **Update secret**
5. The next workflow run will reflect the new count

## Display

The subscriber count appears in the hero section as a glass-morphism badge with:
- 📧 Email icon
- Count in gold with glow effect
- "subscribers already joined" text
- Semi-transparent background with blur effect
