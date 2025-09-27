# 🚀 Deploy EKS Chaos Guardian UI to AWS

**Simple AWS Amplify deployment for hackathon demo**

## 🎯 **Why AWS Amplify?**

✅ **Hackathon Perfect** - Built for frontend demos  
✅ **AWS Native** - Shows AWS expertise  
✅ **Free Tier** - $0-5/month cost  
✅ **Custom Domain** - chaos-guardian.cloudaimldeveops.com  
✅ **SSL Included** - Automatic HTTPS  
✅ **5-Minute Setup** - Fast deployment  

## 📋 **Quick Deployment Steps**

### **1. Run the Deployment Script**
```bash
cd ui
chmod +x deploy-amplify.sh
./deploy-amplify.sh
```

### **2. Deploy to AWS Amplify**
1. Go to [AWS Amplify Console](https://console.aws.amazon.com/amplify/)
2. Click **"Host web app"**
3. Choose **"Deploy without Git provider"**
4. **Upload** all files from `ui/` directory
5. **App name:** `eks-chaos-guardian-demo`
6. **Environment:** `main`
7. **Build settings:** Use `amplify.yml` (already created)

### **3. Add Custom Domain**
1. In Amplify Console → **"Domain management"**
2. Click **"Add domain"**
3. Enter: `chaos-guardian.cloudaimldeveops.com`
4. **Request SSL certificate** (free)
5. **Update DNS** at your domain registrar

### **4. Access Your Demo**
- **URL:** `https://chaos-guardian.cloudaimldeveops.com`
- **Demo ready** in 5-10 minutes!

## 💰 **Cost Breakdown**

| Service | Cost | Notes |
|---------|------|-------|
| AWS Amplify | $0-5/month | Free tier: 1000 build minutes/month |
| Custom Domain | $0 | Your existing domain |
| SSL Certificate | $0 | AWS Certificate Manager (free) |
| **Total** | **$0-5/month** | Perfect for hackathon budget |

## 🎯 **What You Get**

- ✅ **Professional demo site** with hackathon branding
- ✅ **Live scenarios** showcase (6 chaos engineering tests)
- ✅ **AWS tech stack** highlights
- ✅ **Performance metrics** and KPIs
- ✅ **Mobile responsive** design
- ✅ **HTTPS enabled** with custom domain

## 🚨 **Troubleshooting**

**Domain not working?**
- Check DNS propagation (up to 48 hours)
- Verify nameservers at domain registrar
- Ensure SSL certificate is issued

**Build failing?**
- Check `amplify.yml` syntax
- Ensure all files are uploaded
- Check Amplify build logs

## 🏆 **Hackathon Submission Ready**

This deployment gives you:
- ✅ **Public URL** for judges
- ✅ **Professional presentation**
- ✅ **AWS-native architecture**
- ✅ **Cost-optimized solution**
- ✅ **3-minute demo ready**

**Perfect for AWS AI Agent Hackathon!** 🚀
