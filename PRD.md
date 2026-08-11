BUNAPAY — Complete Product Requirements Document (PRD)



Version: 1.0

Date: August 11, 2026

Project Type: P2P USDT/ETB Platform (Telegram Bot → Full Exchange)

Based On: abel-stud/p2p-telegram-bot + abel-stud/p2p-marketplace



1\. Executive Summary



BunaPay is a phased P2P USDT/ETB platform built for Ethiopia. Phase 1 launches as a Telegram bot positioned as a "digital subscription support service" — helping users acquire USDT to pay for Netflix, Spotify, Google Play, and other international subscriptions. The admin (you) is the sole supplier, manually releasing USDT from your Binance wallet after confirming ETB payment via Telebirr.



Long-term vision: Evolve into Ethiopia's most trusted digital asset exchange — the "Binance of Ethiopia" — with a full web/mobile platform, multiple verified traders, automated escrow, and a robust reputation system.



Core Philosophy: Build trust first. Scale later.



2\. Product Vision & Goals



2.1 Vision



To become Ethiopia's most trusted and accessible gateway for digital assets — starting with USDT — serving everyday Ethiopians who need access to global digital services.



2.2 Mission (Phase 1)



Launch a simple, trustworthy Telegram-based service that helps Ethiopians support their digital subscriptions quickly and securely.



2.3 Success Metrics



Metric Phase 1 Target Phase 3 Target

Daily active users 50-100 5,000+

Trade completion rate 95% 98%

Average trade time <30 minutes <10 minutes

Dispute rate <1% <0.5%

User retention (30-day) 60% 75%



3\. Brand Identity



3.1 Brand Profile



Element Detail

Name BunaPay

Tagline (Phase 1) "Support Your Subscriptions. Simply."

Tagline (Phase 3) "Ethiopia's Digital Asset Exchange."

Positioning (Phase 1) Friendly subscription support service

Positioning (Phase 3) Full-featured P2P crypto exchange

Vibe Warm, trustworthy, professional, approachable



3.2 Color Palette



Color Hex Usage

Deep Coffee Brown #3E2723 Primary backgrounds

Warm Cream #F5F5F5 Primary text

Gold #C9A84C Accents, buttons, highlights

Dark Charcoal #1A1A1A Secondary backgrounds



3.3 Tone of Voice



· Friendly but professional

· Clear and simple (no crypto jargon in Phase 1)

· Reassuring and trustworthy

· Focused on service not trading



4\. User Personas



4.1 Phase 1: The Subscriber



· Who: Ethiopian professional or student

· Need: USDT to pay for Netflix, Spotify, Google Play, gaming subscriptions

· Tech level: Low to medium — doesn't understand crypto, doesn't want to

· Trust level: Cautious — needs clear instructions and quick responses

· Pain point: Can't easily get USDT for international services



4.2 Phase 3: The Trader



· Who: Ethiopian crypto enthusiast or small business

· Need: Buy/sell USDT regularly for business or investment

· Tech level: Medium to high — understands wallets and blockchain

· Trust level: Requires reputation system and multiple trader options



4.3 The Admin (You)



· Who: BunaPay founder and operator

· Role: Sole supplier (Phase 1), platform operator (Phase 3)

· Responsibility: Confirm ETB payments, release USDT, manage trusted users, oversee platform growth



5\. Phase 1: Telegram Bot (MVP)



5.1 Core Concept



A Telegram-only bot built on abel-stud/p2p-telegram-bot positioned as a "subscription support service." You are the sole supplier. USDT is manually released from your Binance wallet. No escrow integration.



5.2 User Features



5.2.1 Onboarding



User sends /start — receives warm welcome:



\`\`\`

☕ Welcome to BunaPay!



Need USDT for your Netflix, Spotify, or Google Play subscription?

We've got you covered.



Request subscription support and get USDT in minutes.



👉 What would you like to do?

\`\`\`



5.2.2 Main Menu (Inline Keyboard)



· 📱 REQUEST SUBSCRIPTION SUPPORT

· 📋 MY REQUESTS

· ❓ HOW IT WORKS



5.2.3 Request Flow



1\. User selects "Request Subscription Support"

2\. Bot displays preset amounts: 10, 20, 50, 100 USDT + "Custom Amount"

3\. User selects amount

4\. Bot calculates total in ETB (based on admin-set rate)

5\. User confirms request

6\. Bot asks: "Please provide your BSC (BEP20) wallet address"

7\. User provides wallet address (validated: starts with 0x, 42 characters)

8\. Bot displays payment details:

   \`\`\`

   Send ETB to:

   Telebirr: BunaPay Services

   Number: 09XX XXX XXX

   Amount: X,XXX ETB

   

   Upload your payment screenshot below when done.

   \`\`\`

9\. User pays ETB and uploads screenshot

10\. Bot notifies admin (you) with trade details and screenshot

11\. Admin confirms ETB receipt → manually sends USDT from Binance

12\. Admin uses /complete\_request #ID \[TX\_HASH]

13\. User receives confirmation:

    \`\`\`

    🚀 Subscription Support Complete!

    

    Your USDT has been sent to:

    0x1234...abcd

    

    Transaction Hash:

    0x5678...efgh

    

    Your subscriptions are ready! ☕

    \`\`\`



5.2.4 Transaction History



User can view all past requests with status:



· ⏳ PENDING PAYMENT

· ✅ PAYMENT CONFIRMED

· 🚀 COMPLETED



5.3 Admin Features



All admin commands are restricted to TELEGRAM\_ADMIN\_ID only.



Command Purpose

/dashboard View all pending requests

/confirm\_payment #ID Confirm ETB payment received

/complete\_request #ID \[TX\_HASH] Mark complete with transaction hash

/set\_rate Update USDT/ETB exchange rate

/trusted\_list View trusted users list

/add\_trusted @username Add user to trusted list

/remove\_trusted @username Remove user from trusted list

/block\_user @username Block a user

/unblock\_user @username Unblock a user



5.4 Language Guidelines (Phase 1)



Instead of... Use...

Buy/Sell USDT Request subscription support

Trade Request

Exchange Platform

Order Support request

Release funds Complete support

Escrow We hold USDT to ensure delivery

Merchant/Supplier Support partner



5.5 Legal Positioning



Include in user communications:



\`\`\`

Terms of Service:

BunaPay helps users support their digital subscriptions.

We are not a financial institution or crypto exchange.

USDT is provided as a service to support subscription payments.

\`\`\`



6\. Phase 2: Telegram Bot + Whitelisted Suppliers



6.1 Core Concept



Add a small group of trusted suppliers (friends/partners) to the Telegram bot. You remain the admin controlling fund release.



6.2 New Features



Supplier Whitelist:



· Only users in TRUSTED\_SUPPLIERS list can post offers

· Each supplier must pre-fund USDT to your escrow wallet before posting



Commission System:



· Admin takes 0.5-1.5% commission on each supplier's trade

· Automated calculation and deduction



Supplier Commands:



· /post\_offer — Create a sell offer (whitelisted only)

· /my\_offers — View active offers

· /offer\_history — View completed offers



Admin Enhancements:



· /approve\_supplier @username — Add to whitelist

· /remove\_supplier @username — Remove from whitelist

· /set\_commission \[%] — Adjust commission rate

· /supplier\_dashboard — View all supplier activity



6.3 Escrow Introduction



Suppliers must transfer USDT to your escrow wallet before posting offers. You control the escrow wallet. This ensures funds are available before trades go live.



7\. Phase 3: Full-Scale Exchange Platform



7.1 Core Concept



The complete abel-stud/p2p-marketplace platform — a full web application with React frontend, FastAPI backend, and Telegram bot integration. This is your "Binance of Ethiopia."



7.2 Platform Features



Web Interface (React + Vite):



· Mobile-responsive design

· Browse buy/sell offers with live updates

· Post trade advertisements

· Complete trade management workflow

· User verification system



Backend (FastAPI + SQLAlchemy):



· RESTful API for all platform operations

· Secure escrow system with admin-controlled release

· Automated 1.5% commission calculation

· Audit logging with complete transaction history

· Trade timeout: 90-minute automatic expiration



Telegram Bot Integration:



· Full trade management through Telegram

· Real-time admin notifications for new deals and confirmations

· Sellers confirm payments via bot

· Admin releases USDT through bot commands



Admin Panel:



· Comprehensive admin panel for platform management

· Monitor all platform activity

· User management and verification

· Release funds manually after payment confirmation



7.3 Multi-Trader Support



· Multiple verified traders can post offers

· Reputation system for traders and buyers

· Dispute resolution workflow

· Tiered commission structure (lower rates for high-volume traders)



7.4 Mobile App (Future)



· React Native or Flutter mobile app

· Push notifications for trade updates

· Biometric authentication



8\. Technical Architecture



8.1 Phase 1 Architecture (Telegram Bot Only)



\`\`\`

┌─────────────────────────────────────────────────────────────┐

│                      TELEGRAM USERS                         │

└─────────────────────────┬───────────────────────────────────┘

                          │

                          ▼

┌─────────────────────────────────────────────────────────────┐

│              TELEGRAM BOT API                              │

│         (python-telegram-bot library)\[reference:26]            │

└─────────────────────────┬───────────────────────────────────┘

                          │

                          ▼

┌─────────────────────────────────────────────────────────────┐

│              BUNAPAY BOT (Python 3.11+)                    │

│  ┌─────────────────────────────────────────────────────┐   │

│  │  Command Handlers  │  Business Logic  │  Database  │   │

│  │  /start, /request  │  Trade Mgmt     │  SQLite    │   │

│  │  /dashboard        │  Rate Calc      │  (WAL)     │   │

│  │  /confirm\_payment  │  Validation     │            │   │

│  │  /complete\_request │  Logging        │            │   │

│  └─────────────────────────────────────────────────────┘   │

└─────────────────────────┬───────────────────────────────────┘

                          │

                          ▼

┌─────────────────────────────────────────────────────────────┐

│                   EXTERNAL SYSTEMS                          │

│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │

│  │   Binance    │  │   Telebirr   │  │   BSC        │     │

│  │  (USDT       │  │  (ETB        │  │  (Wallet     │     │

│  │   Wallet)    │  │   Payments)  │  │   Addresses) │     │

│  └──────────────┘  └──────────────┘  └──────────────┘     │

└─────────────────────────────────────────────────────────────┘

\`\`\`



8.2 Phase 3 Architecture (Full Platform)



\`\`\`

┌─────────────────────────────────────────────────────────────┐

│                    USERS (Web + Mobile)                     │

└─────────────────────────┬───────────────────────────────────┘

                          │

        ┌─────────────────┼─────────────────┐

        │                 │                 │

        ▼                 ▼                 ▼

┌───────────────┐ ┌───────────────┐ ┌───────────────┐

│  React        │ │  Telegram     │ │  Mobile App   │

│  Frontend     │ │  Bot          │ │  (Future)     │

│  (Vercel)\[reference:27]│ │  (Railway)\[reference:28]│ │               │

└───────┬───────┘ └───────┬───────┘ └───────┬───────┘

        │                 │                 │

        └─────────────────┼─────────────────┘

                          │

                          ▼

┌─────────────────────────────────────────────────────────────┐

│              FASTAPI BACKEND (Render/Railway)\[reference:29]  │

│  ┌─────────────────────────────────────────────────────┐   │

│  │  API Routes  │  Services  │  Repositories  │ Models │   │

│  │  /trades     │  Trade     │  TradeRepo     │ User   │   │

│  │  /users      │  User      │  UserRepo      │ Trade  │   │

│  │  /admin      │  Payment   │  PaymentRepo   │ Offer  │   │

│  │  /listings   │  Commission│  OfferRepo     │        │   │

│  └─────────────────────────────────────────────────────┘   │

└─────────────────────────┬───────────────────────────────────┘

                          │

                          ▼

┌─────────────────────────────────────────────────────────────┐

│              DATABASE LAYER                                 │

│  ┌─────────────────────────────────────────────────────┐   │

│  │  SQLAlchemy ORM\[reference:30]                             │   │

│  │  ┌─────────────────────────────────────────────┐   │   │

│  │  │  SQLite (Phase 1) → PostgreSQL (Phase 3)   │   │   │

│  │  │  (Supabase / AWS RDS)                       │   │   │

│  │  └─────────────────────────────────────────────┘   │   │

│  └─────────────────────────────────────────────────────┘   │

└─────────────────────────────────────────────────────────────┘

\`\`\`



8.3 Technology Stack Summary



Layer Phase 1 Phase 3

Language Python 3.11+ Python 3.11+

Bot Framework python-telegram-bot python-telegram-bot

Backend None (bot only) FastAPI with SQLAlchemy ORM

Frontend None React with Vite

Database SQLite (WAL mode) SQLite → PostgreSQL

ORM None (or simple sqlite3) SQLAlchemy

Deployment Railway Vercel/Netlify + Render/Railway

Blockchain Manual (Binance) tron-python or solathon

Monitoring Logging + UptimeRobot Logging + Sentry + UptimeRobot



9\. Database Design



9.1 Phase 1 Schema (SQLite)



users



Column Type Description

id INTEGER Primary key

telegram\_id TEXT Unique Telegram user ID

username TEXT Telegram username

first\_name TEXT User's first name

is\_trusted INTEGER 0=no, 1=yes

is\_blocked INTEGER 0=no, 1=yes

total\_requests INTEGER Number of requests made

total\_spent\_etb REAL Total ETB spent

created\_at DATETIME Registration timestamp



requests (trades)



Column Type Description

id TEXT Unique request ID (e.g., #BUN-001)

user\_id INTEGER Foreign key to users

amount\_usdt REAL USDT amount requested

amount\_etb REAL ETB amount paid

wallet\_address TEXT User's BSC wallet address

status TEXT pending, paid, completed

payment\_screenshot TEXT File path or URL

tx\_hash TEXT Blockchain transaction hash

admin\_notes TEXT Internal notes

created\_at DATETIME Request creation time

paid\_at DATETIME Payment confirmation time

completed\_at DATETIME Completion time



rate\_settings



Column Type Description

id INTEGER Primary key

usdt\_to\_etb REAL Current exchange rate

updated\_at DATETIME Last update time

updated\_by TEXT Admin who updated



9.2 Phase 3 Additions



offers (for multi-supplier)



Column Type Description

id INTEGER Primary key

supplier\_id INTEGER Foreign key to users

amount\_usdt REAL USDT amount offered

price\_etb REAL Price per USDT

status TEXT active, filled, cancelled

created\_at DATETIME Offer creation time



transactions (audit log)



Column Type Description

id INTEGER Primary key

request\_id TEXT Related request

action TEXT created, paid, released, etc.

actor\_id INTEGER User who performed action

details TEXT JSON with additional data

created\_at DATETIME Action timestamp



10\. Security Requirements



10.1 Core Security Principles



1\. Never trust user input — validate everything

2\. Principle of least privilege — minimum access for every role

3\. Defense in depth — multiple layers of security

4\. Audit everything — log all critical actions



10.2 Admin Command Protection



· All admin commands restricted to TELEGRAM\_ADMIN\_ID

· RELEASE\_SECRET environment variable for additional authorization

· No fund release without explicit admin command



10.3 Data Security



· All secrets in .env file (never in code)

· Database file permissions: 600 (read/write for owner only)

· SQLite WAL mode for write safety

· Daily automated backups



10.4 Payment Security



· Manual verification required — USDT never released without confirmed ETB receipt

· Payment screenshots stored securely

· All payment details logged for audit



10.5 User Security



· Blocked users cannot make requests

· Trusted users list for faster processing

· Rate limiting to prevent abuse

· All actions logged with user ID and timestamp



10.6 Telebirr Anonymity Options



Option How It Works Risk Level

Business Telebirr account Register as merchant/agent. Business name appears. Low — professional

Trusted agent Agent receives payments on your behalf. Medium — agent trust

Secondary phone number Register with number not linked to main identity. Medium — still requires ID

Rotate numbers Use multiple Telebirr numbers and rotate. High — complex



Recommendation: Register a business Telebirr account under your company or brand name.



11\. Deployment Strategy



11.1 Phase 1 Deployment (Railway)



Steps:



1\. Fork/clone abel-stud/p2p-telegram-bot

2\. Configure .env with bot token and admin ID

3\. Deploy to Railway (free tier)

4\. Set up UptimeRobot for health monitoring



Railway Configuration:



\`\`\`

TELEGRAM\_BOT\_TOKEN=your\_token

TELEGRAM\_ADMIN\_ID=your\_id

RELEASE\_SECRET=your\_secret

DATABASE\_URL=sqlite:///./bunapay.db

\`\`\`



11.2 Phase 3 Deployment



Frontend: Vercel/Netlify (free tier)

Backend: Render/Railway (free tier)

Database: Supabase PostgreSQL (free tier — 500MB)



Environment Variables (Backend):



\`\`\`

DATABASE\_URL=postgresql://...

ESCROW\_WALLET\_ADDRESS=TXxxxxxx

COMMISSION\_PERCENT=1.5

RELEASE\_SECRET=secure\_key\_here

TELEGRAM\_ADMIN\_ID=123456789

\`\`\`



Environment Variables (Telegram Bot):



\`\`\`

TELEGRAM\_BOT\_TOKEN=your\_bot\_token\_here

TELEGRAM\_ADMIN\_ID=123456789

BACKEND\_URL=https\://your-backend.onrender.com

RELEASE\_SECRET=secure\_key\_here

\`\`\`



11.3 Scaling Path



Stage Users/Day Database Hosting Cost

Launch <50 SQLite Railway Free $0

Growth 50-200 SQLite Railway Paid (\~$5/mo) $5/mo

Scaling 200-1000 Supabase PostgreSQL Railway + Supabase \~$15/mo

Enterprise 1000+ AWS RDS PostgreSQL VPS + Managed DB \~$50+/mo



12\. Monitoring & Maintenance



12.1 Phase 1 Monitoring



Essential:



· Python logging module (all actions logged)

· UptimeRobot (free — checks bot responsiveness)

· Manual daily health check (run /dashboard)



Nice to have:



· Sentry (free tier — error tracking)

· Custom /health command



12.2 Phase 3 Monitoring



Add:



· Sentry for error tracking

· Prometheus + Grafana for metrics (optional)

· Automated backup verification

· Scheduled health checks on all services



12.3 Maintenance Tasks



Task Frequency Responsibility

Check pending requests Hourly Admin

Verify wallet balance Daily Admin

Database backup Daily Automated

Review logs for issues Daily Admin

Update exchange rate As needed Admin

Software updates Monthly Admin



13\. Phased Roadmap



Phase 1: MVP (Month 1-2)



Goal: Launch and validate the model



Milestone Timeline

Deploy Telegram bot on Railway Week 1

Configure admin commands Week 1

Test with 5-10 friends Week 2

Soft launch (invite-only) Week 3

Public launch Week 4

Reach 50 daily users Month 2



Success criteria: 50+ active users, <1% dispute rate, positive feedback



Phase 2: Trusted Suppliers (Month 3-6)



Goal: Scale supply without losing trust



Milestone Timeline

Whitelist system implementation Month 3

Onboard 3-5 trusted suppliers Month 3-4

Commission system live Month 4

Reach 200 daily users Month 6



Success criteria: 200+ daily users, 5+ active suppliers, <0.5% dispute rate



Phase 3: Full Platform (Month 7-12)



Goal: Launch the "Binance of Ethiopia"



Milestone Timeline

Deploy p2p-marketplace full stack Month 7-8

Migrate database to PostgreSQL (Supabase) Month 8

Launch web interface Month 9

Public launch of full platform Month 10

Reach 1,000+ daily users Month 12



Success criteria: 1,000+ daily users, 50+ verified traders, <0.3% dispute rate



Phase 4: Expansion (Year 2+)



Goal: Market leadership



Milestone Timeline

Mobile app launch Year 2 Q1

Additional cryptocurrencies (BTC, ETH) Year 2 Q2

Advanced trading features Year 2 Q3

ETB stablecoin integration Year 2 Q4

Regional expansion Year 3+



14\. Risk Assessment



Risk Impact Probability Mitigation

NBE regulatory action Critical Medium Legal consultation; business Telebirr; subscription positioning

Scammer attempts High High Manual verification; trusted users list; transaction limits (<$100)

Technical failure Medium Low Regular backups; monitoring; redundancy planning

Supplier default High Low (Phase 1) You are the only supplier; future suppliers must pre-fund escrow

Reputation damage High Medium Fast support; transparent communication; dispute resolution

Payment disputes Medium Medium Screenshot verification; clear terms; chat history



15\. Success Metrics & KPIs



15.1 Phase 1 KPIs



Metric Target

Daily active users 50+

Trade completion rate 95%

Average trade time <30 minutes

Dispute rate <1%

User retention (30-day) 60%

Net Promoter Score 40



15.2 Phase 3 KPIs



Metric Target

Daily active users 1,000+

Monthly trading volume $100,000+

Trade completion rate 98%

Average trade time <10 minutes

Dispute rate <0.3%

Verified traders 50+

Platform fee revenue Sustainable



16\. Appendix: Command Reference



Phase 1 User Commands



Command Description

/start Welcome and main menu

/request Start a subscription support request

/my\_requests View request history

/help Help and instructions



Phase 1 Admin Commands



Command Description

/dashboard View pending requests

/confirm\_payment #ID Confirm ETB payment received

/complete\_request #ID \[TX\_HASH] Mark request complete

/set\_rate Update USDT/ETB rate

/trusted\_list View trusted users

/add\_trusted @username Add trusted user

/block\_user @username Block user



Phase 3 Additional Commands



Command Description

/post\_offer Create sell offer (suppliers)

/my\_offers View active offers

/approve\_supplier @username Approve supplier (admin)

/set\_commission \[%] Set commission rate (admin)

/supplier\_dashboard Supplier activity view (admin)



17\. Conclusion



BunaPay is designed as a phased, scalable platform that starts as a simple Telegram bot and evolves into Ethiopia's most trusted digital asset exchange.



Phase 1 validates the business model with minimal risk — you as the sole supplier, manual USDT release, and "subscription support" positioning.



Phase 2 adds trusted suppliers to scale volume while maintaining trust.



Phase 3 launches the full abel-stud/p2p-marketplace platform — a complete web + mobile experience with automated escrow, multiple traders, and robust reputation systems.



The technology is ready. The abel-stud projects provide battle-tested architecture. Your job is to execute, build trust, and scale deliberately.



\---



Ready to build, boss. 🚀☕

\
