This repo is trying to find correlation between social media sentiment to stock price.
The focus is on stocks that experienced rally, meaning hundreds of percentage increase in few months.
Files:
1. Get_Stock_Data.py - Enables you to download financial data for specific stock for specific dates
2. GetFromBrightDataTheRedditStockRelatedPosts.py - Enables you to download reddit posts related to the specific stock. We are using bright data interface, which is free up to a certain amount of tokens. you need to open an account in bright data.
3. CalculateRedditSentimentPerStock.R - Calcualting sentiment per stock for each date in the defined range
