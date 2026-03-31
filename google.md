# 🔐 How to Set Up Google Sign-In for CHRS

This guide walks you through creating a **Google OAuth 2.0 Client ID** so that students can sign in to the KKWIEER College Hall Reservation System using their `@kkwagh.edu.in` Google accounts.

---

## Prerequisites

- A Google account (any Gmail will work for setup)
- Access to [Google Cloud Console](https://console.cloud.google.com/)

---

## Step 1: Create a Google Cloud Project

1. Go to **[Google Cloud Console](https://console.cloud.google.com/)**
2. Click the **project dropdown** at the top-left (next to "Google Cloud")
3. Click **"New Project"**
4. Enter the following:
   - **Project Name**: `CHRS-KKWIEER` (or any name you prefer)
   - **Organization**: Leave as default
5. Click **"Create"**
6. Wait for the project to be created, then **select it** from the project dropdown

---

## Step 2: Configure the OAuth Consent Screen

Before creating credentials, you must configure the consent screen that users see when signing in.

1. In the left sidebar, go to **APIs & Services → OAuth consent screen**
2. Select **"External"** as the User Type (this works for `@kkwagh.edu.in` Google Workspace accounts)
3. Click **"Create"**
4. Fill in the required fields:

   | Field | Value |
   |-------|-------|
   | **App name** | `KKWIEER Hall Reservation` |
   | **User support email** | Your email address |
   | **App logo** | *(Optional)* Upload the KKW logo |
   | **Developer contact email** | Your email address |

5. Click **"Save and Continue"**

### Scopes

6. On the **Scopes** page, click **"Add or Remove Scopes"**
7. Select these scopes:
   - `email`
   - `profile`
   - `openid`
8. Click **"Update"**, then **"Save and Continue"**

### Test Users (Optional for development)

9. You can add test users here (your `@kkwagh.edu.in` email)
10. Click **"Save and Continue"**
11. Review the summary and click **"Back to Dashboard"**

---

## Step 3: Create OAuth 2.0 Client ID

1. In the left sidebar, go to **APIs & Services → Credentials**
2. Click **"+ CREATE CREDENTIALS"** at the top
3. Select **"OAuth client ID"**
4. Configure as follows:

   | Field | Value |
   |-------|-------|
   | **Application type** | `Web application` |
   | **Name** | `CHRS Web Client` |

5. Under **Authorized JavaScript origins**, add these URLs:

   ```
   http://localhost:5000
   http://localhost:3000
   ```

   > ⚠️ **For production**, also add your deployed domain, e.g.:
   > ```
   > https://your-domain.com
   > ```

6. Under **Authorized redirect URIs**, add:

   ```
   http://localhost:5000
   http://localhost:3000
   ```

7. Click **"Create"**

---

## Step 4: Copy Your Client ID

After creating the credentials, a dialog will appear showing:

- **Client ID**: Something like `123456789-abc123def456.apps.googleusercontent.com`
- **Client Secret**: (Not needed for this project)

📋 **Copy the Client ID** — you'll need it in the next step.

---

## Step 5: Add Client ID to Your Project

### Option A: Update the `.env` file (Backend)

Open `backend/.env` and replace the placeholder:

```env
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID_HERE
```

With your actual Client ID:

```env
GOOGLE_CLIENT_ID=123456789-abc123def456.apps.googleusercontent.com
```

### That's it! 🎉

The backend serves the Client ID to the frontend automatically via the `/api/auth/google-client-id` endpoint. No frontend changes needed.

---

## Step 6: Test Google Sign-In

1. Start the backend server:
   ```bash
   cd backend
   python app.py
   ```

2. Open **http://localhost:5000** in your browser

3. Make sure **"Student"** is selected in the Login As dropdown

4. Click **"Sign in with Google"**

5. A Google popup will appear — sign in with a `@kkwagh.edu.in` account

6. If the email domain is correct, you'll be logged in automatically!

> ⚠️ **Important**: Only `@kkwagh.edu.in` email addresses are allowed. Any other Google account will be rejected with an error message.

---

## Troubleshooting

### "Google Sign-In is not configured yet"
- You haven't added your Client ID to `backend/.env`
- Make sure to restart the Flask server after editing `.env`

### "popup_closed_by_user" error
- The user closed the Google popup before completing sign-in
- Try again and complete the sign-in flow

### "Only @kkwagh.edu.in email addresses are allowed"
- The user signed in with a non-college Google account
- They need to use their official college email

### "Invalid Google token"
- The token expired or was tampered with
- Try signing in again

### Google popup doesn't appear
- Check browser popup blocker settings
- Make sure `https://accounts.google.com/gsi/client` script is loading (check browser console)
- Verify your Client ID is correct in `.env`

### "redirect_uri_mismatch" error
- Go back to Google Cloud Console → Credentials → Edit your OAuth client
- Add your current URL (e.g., `http://localhost:5000`) to **Authorized JavaScript origins**

---

## For Production Deployment

When deploying to a live server:

1. Go to **Google Cloud Console → Credentials → Edit your OAuth client**
2. Add your production domain to:
   - **Authorized JavaScript origins**: `https://your-domain.com`
   - **Authorized redirect URIs**: `https://your-domain.com`
3. Update `backend/.env` on your server with the same Client ID
4. Consider publishing the OAuth consent screen (APIs & Services → OAuth consent screen → **Publish App**)

---

## Quick Reference

| Item | Location |
|------|----------|
| Google Cloud Console | https://console.cloud.google.com/ |
| OAuth Credentials | APIs & Services → Credentials |
| Consent Screen | APIs & Services → OAuth consent screen |
| Client ID in project | `backend/.env` → `GOOGLE_CLIENT_ID` |
| Backend endpoint | `GET /api/auth/google-client-id` |
| Token verification | `POST /api/auth/google` |

---

*Last updated: March 2026*
