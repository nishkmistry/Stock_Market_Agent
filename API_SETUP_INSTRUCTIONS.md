# API Key Setup Instructions for Finance Agent

## Required API Keys

To make the Finance Agent fully functional, you need to obtain and configure the following API keys:

### 1. GNews API Key (for financial news)
- Get it from: https://gnews.io/
- Set as: `GNEWS_API_KEY=your_actual_gnews_key_here`

### 2. Marketaux API Key (for financial news)
- Get it from: https://marketaux.com/
- Set as: `MARKETAUX_API_KEY=your_actual_marketaux_key_here`

### 3. Groq API Key (for LLM agent)
- Get it from: https://groq.com/
- Set as: `GROQ_API_KEY=your_actual_groq_api_key_here`

## Setup Instructions

1. Create a `.env` file in the project root directory (same level as this README)
2. Add the following lines to the `.env` file:

```
GROQ_API_KEY=your_actual_groq_api_key_here
GNEWS_API_KEY=your_actual_gnews_key_here
MARKETAUX_API_KEY=your_actual_marketaux_key_here
```

3. Replace the placeholder values with your actual API keys obtained from the respective services
4. Save the file
5. Restart the server if it's currently running

## Important Notes

- **Never commit your `.env` file to version control** - it contains sensitive API keys
- The `.gitignore` file is already configured to exclude `.env` files
- If you accidentally commit your `.env` file, you'll need to rotate all your API keys immediately
- Free tiers of these APIs may have rate limits - if you encounter quota errors, wait a few minutes before trying again
- The Groq API key is required for the agent to function - without it, the agent will not be able to reason and act
- The news API keys are optional for basic stock data functionality, but enhance the agent's capabilities

## Testing Your Setup

After configuring your API keys, you can test the agent directly:

```bash
python agent.py
```

This should run a test query and show you the agent's reasoning process.

## Troubleshooting

If you encounter "API key not valid" errors:
1. Double-check that your API keys are correctly copied
2. Ensure there are no extra spaces or characters in the .env file
3. Verify that the API keys are active and not expired
4. Check that you're using the correct API key for each service

If you encounter quota exceeded errors:
1. Wait a few minutes before trying again
2. Consider upgrading your API plan if you need higher usage limits
3. The agent will automatically handle quota errors and inform you to try again later