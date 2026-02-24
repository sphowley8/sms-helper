# SMS → Strava Updater (Python, AWS, 1 User)

A minimal, low-cost system that allows you to update your Strava activities via SMS.

No frontend.  
No database.  
Single user (you).  
Hosted on AWS.  

---

# 💰 Cost Breakdown

## AWS (Very Low Usage)

| Service | Estimated Monthly Cost |
|----------|------------------------|
| Lambda | $0 (covered by free tier) |
| API Gateway (optional) | ~$0 |
| Secrets Manager | ~$0.40 |
| CloudWatch Logs | Pennies |
| **Total AWS** | **$0–$2/month** |

You can reduce this further by:
- Using Lambda Function URLs instead of API Gateway
- Storing secrets in environment variables instead of Secrets Manager

---

## SMS Provider (Primary Cost)

Using Twilio:

- ~$0.007–$0.008 per SMS (sent or received)
- ~$1/month for a phone number

### Example Usage

| Messages/Month | Estimated Cost |
|----------------|----------------|
| 50 | ~$1.50–$2 |
| 200 | ~$3–$5 |

**Total realistic monthly cost: $2–$8**

---

# 🧱 Architecture
