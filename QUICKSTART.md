# 🚀 FINBOT Quick Start Guide

## Installation (3 minutes)

### Step 1: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set Up Groq API Key

1. Visit [https://console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Generate an API key
4. Create `.env` file:
   ```bash
   cp .env.example .env
   ```
5. Edit `.env` and paste your API key:
   ```
   GROQ_API_KEY=gsk_your_actual_api_key_here
   ```

### Step 3: Run the Application
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## First Time Usage (2 minutes)

### Try Analysis Mode

1. **Prepare a sample CSV file** with financial data (or use your own)
   - Example columns: Date, Description, Amount, Category
   - Save as `my_finances.csv`

2. **Upload the file**
   - Click "Browse files" button
   - Select your CSV file
   - Wait for processing

3. **View data overview**
   - Check the metrics (rows, columns, completeness)
   - Expand "View Sample Data" to see your data

4. **Run analysis**
   - Click "🚀 Analyze Data"
   - Wait 5-10 seconds for AI analysis
   - Review the results:
     - Financial Health Score
     - Risk Level
     - Key Insights
     - Recommendations

### Try Chatbot Mode

1. **Switch to Chatbot mode**
   - In the sidebar, select "💬 Chatbot Q&A"

2. **Ask questions** (examples)
   ```
   What is the total amount in my dataset?
   Show me the top 5 expenses
   What are the main spending categories?
   How much did I spend last month?
   What trends do you see?
   ```

3. **Have a conversation**
   - Ask follow-up questions
   - The bot remembers context
   - Get detailed, data-driven answers

## Example CSV Format

Create a file called `sample_finances.csv`:

```csv
Date,Description,Amount,Category,Type
2024-01-01,Salary,5000,Income,Credit
2024-01-02,Rent,1500,Housing,Debit
2024-01-03,Groceries,200,Food,Debit
2024-01-04,Electric Bill,80,Utilities,Debit
2024-01-05,Restaurant,45,Food,Debit
2024-01-10,Freelance,500,Income,Credit
2024-01-15,Gas,60,Transportation,Debit
2024-01-20,Shopping,150,Entertainment,Debit
```

## Common Questions

**Q: Do I need to pay for Groq?**
A: No! Groq offers a generous free tier that's perfect for FINBOT.

**Q: Is my data secure?**
A: Yes! All data is processed locally. Only anonymized summaries are sent to Groq for analysis.

**Q: Can I use my own LLM instead of Groq?**
A: Yes! The code is modular. You can modify `src/agents/` files to use any LangChain-compatible LLM.

**Q: How do I clear my conversation history?**
A: Click "🗑️ Clear Conversation" in Chatbot mode, or delete files in `data/memory/`

**Q: What file formats are supported?**
A: CSV (.csv), Excel (.xlsx, .xls)

## Tips for Best Results

1. **Clean your data first**
   - Remove empty rows/columns
   - Ensure consistent date formats
   - Use clear column names

2. **Use descriptive column names**
   - Good: "Monthly_Revenue", "Total_Expenses"
   - Bad: "Col1", "X", "Data"

3. **Include date columns**
   - Enables trend analysis
   - Better insights

4. **Ask specific questions**
   - Good: "What was my total income in January?"
   - Bad: "Tell me stuff"

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the code in `src/` to understand the architecture
- Customize settings in `config/settings.py`
- Star the repository if you find it helpful! ⭐

## Need Help?

- Check the [README.md](README.md) for troubleshooting
- Review the code comments for implementation details
- Create an issue on GitHub

---

**Happy analyzing! 📊💰**
