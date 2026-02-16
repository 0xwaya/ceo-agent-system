# 🚀 Quick Start - Graph Dashboard

## Access the New UI

- Landing Dashboard: `http://localhost:5001/`
- Graph Dashboard: `http://localhost:5001/graph`
- Admin Dashboard: `http://localhost:5001/admin`
- Full Reports (direct): `http://localhost:5001/reports`

---

## 🎨 What You'll See

### 1. **Dark Modern Interface**
- Navy blue background (#0a0e27)
- Consistent gray scale design
- Smooth animations
- Professional typography

### 2. **Six Main Sections**

#### a. **Configuration Form** (Top)
Fill in your project details:
- Company Name
- Industry (dropdown)
- Location
- Total Budget ($1K - $1M)
- Timeline (30-365 days)
- Strategic Objectives (multiple lines)

#### b. **Agent Status Grid** (Middle Left)
Real-time status cards for:
- 👔 CEO - Master Orchestrator
- 💰 CFO - Financial Analysis
- 🛠️ Engineer - Technical Implementation
- 🔍 Researcher - Market Research
- ⚖️ Legal - Compliance (Future)
- 📱 MarTech - Marketing Tech (Future)

#### c. **Progress Bar** (Middle Right)
- Visual progress indicator
- Current phase display
- Percentage complete

#### d. **Terminal Output** (Bottom Left)
- Real-time execution log
- Color-coded messages
- Auto-scrolling

#### e. **Results Summary** (Bottom Right)
- Metrics dashboard
- Agent summaries
- Key findings
- Recommendations

---

## 📝 How to Use

### Step 1: Fill the Form
```
Company Name: TechCorp Inc
Industry: Software & Technology
Location: San Francisco, CA
Total Budget: 100000
Timeline: 90
Objectives:
  Launch SaaS platform
  Build enterprise sales team
  Establish market presence
```

### Step 2: Click "Execute Multi-Agent System"
The system will:
1. Validate your inputs
2. Start the CEO orchestrator
3. Route tasks to CFO, Engineer, Researcher
4. Execute each subgraph sequentially
5. Consolidate results

### Step 3: Watch Real-Time Updates
- Agent badges change: Idle → Active → Completed
- Progress bar fills: 0% → 100%
- Terminal shows live messages
- Phase indicator updates

### Step 4: Review Results
- Check completed phases count
- See executive decisions made
- Review budget remaining
- Read agent summaries with findings

### Step 5: Download Report (Optional)
Click "Download Report" to save JSON results

---

## 🎯 Features

### ✅ Working Now
- Dark theme UI
- Form validation
- WebSocket real-time updates
- Agent status tracking
- Progress visualization
- Terminal output streaming
- Results display
- Report download
- Checkpoint resumption (enter Thread ID)

### 🔜 Coming Soon
- Legal agent integration
- MarTech agent integration
- Approval workflow UI
- Chat interface
- Execution history

---

## 🐛 Troubleshooting

### Issue: Dashboard doesn't load
**Solution**: Check Flask is running on port 5001
```bash
lsof -ti:5001  # Should return process ID
```

### Issue: VS Code Simple Browser shows blank page
**Solution**: restart the Flask app after pulling latest changes (development embedding headers were adjusted for VS Code webviews)
```bash
pkill -f "python app.py" || true
/Users/pc/code/langraph/.venv/bin/python app.py
```

### Issue: No real-time updates
**Solution**: Check WebSocket connection in browser console
```javascript
// Should see: "Connected to server"
```

### Issue: Execution fails
**Solution**: Check terminal for errors
```bash
# View logs
curl http://localhost:5001/api/logs
```

### Issue: Form validation errors
**Solution**: Check requirements:
- Budget: $1,000 - $1,000,000
- Timeline: 30 - 365 days
- At least 1 objective

---

## 🎓 Tips

### 1. **Use Realistic Budgets**
- Startup: $50K - $100K
- SMB: $100K - $500K
- Enterprise: $500K - $1M

### 2. **Set Appropriate Timelines**
- Quick launch: 30-60 days
- Standard project: 90-180 days
- Complex initiative: 180-365 days

### 3. **Write Clear Objectives**
Use action-oriented language:
- ✅ "Launch SaaS platform"
- ✅ "Build 5-person sales team"
- ❌ "Make money"
- ❌ "Be successful"

### 4. **Resume Executions**
If execution stops:
1. Note the Thread ID from terminal
2. Enter it in "Thread ID" field
3. Click Execute to continue

### 5. **Monitor Budget**
- CFO analyzes budget, doesn't spend
- Engineer estimates costs for tech stack
- Researcher identifies market opportunities
- CEO makes final budget decisions

---

## 📊 Example Results

After execution, you'll see metrics like:

```
Completed Phases: 7
Executive Decisions: 12
Budget Remaining: $85,000
```

And agent summaries:

**CFO Summary**
- ✅ Budget analysis complete
- ✅ Compliance checks passed
- 💡 Recommendation: Allocate $15K to marketing

**Engineer Summary**
- 🛠️ Tech stack: React, Node.js, PostgreSQL
- 📦 Code files: 3 components, 550 LOC
- 🧪 Test coverage: 85%
- 📋 Deployment plan: AWS ECS

**Researcher Summary**
- 🔍 Documents analyzed: 3 competitors
- 📊 Key findings: 7 insights
- 🎯 Opportunities: B2B SaaS, Enterprise focus
- ⚠️ Risks: Market saturation

---

## 🔗 Related Links

- **Main README**: [README.md](README.md)
- **Graph Architecture Docs**: [graph_architecture/README.md](graph_architecture/README.md)
- **Full Implementation Details**: [GRAPH_UI_IMPLEMENTATION.md](docs/GRAPH_UI_IMPLEMENTATION.md)
- **API Documentation**: `http://localhost:5001/docs`

---

## 💬 Need Help

1. Check the [GRAPH_UI_IMPLEMENTATION.md](docs/GRAPH_UI_IMPLEMENTATION.md) for detailed docs
2. View logs at `http://localhost:5001/api/logs`
3. Review terminal output where Flask is running
4. Check browser console for JavaScript errors (F12)

---

**Happy Orchestrating! 🎉**
