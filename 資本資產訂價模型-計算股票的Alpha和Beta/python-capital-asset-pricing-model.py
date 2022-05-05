# -*- coding: utf-8 -*-
"""
Created on Sun May  1 21:17:21 2022

@author: Alice

reference:
資本資產訂價模型-計算股票的Alpha和Beta(Capital Asset Pricing Model, CAPM)
https://ycy-blog.herokuapp.com/article/python-capital-asset-pricing-model/
"""

  
    
import pandas as pd
import yfinance as yf
import statsmodels.api as sm

#0050
url = "https://www.yuantaetfs.com/api/StkWeights?date=&fundid=1066"
df = pd.read_json(url)
df.info()

#get 50 stock price
data = {}
for x in df['code']:
  stock_no = f"{x}.tw"
  data[stock_no] = yf.download(stock_no, start='2020-01-01')

#get 50 Adj Close  
df_adj = pd.DataFrame()
for x in data:
  df_adj[x] = data[x]['Adj Close']

#get stock index ^TWII
stockindex = yf.download('^TWII', start='2020-01-01')

#merge data
df = pd.DataFrame()
df = pd.merge(stockindex[['Adj Close']], df_adj, how = 'left', on = 'Date').dropna(axis=0)
df.rename(columns={'Adj Close':'TWII'},inplace=True)

#use each stock return runs a regression on index
ret_df = df.pct_change().dropna(axis=0)
final_output = {}
alpha_list = []
beta_list = []

for company in ret_df.columns[1:]:
    X = ret_df[['TWII']].assign(Intercept=1)
    Y = ret_df[company]
    X1 = sm.add_constant(X)     
    model = sm.OLS(Y, X1)
    results = model.fit()
    alpha = pd.read_html(results.summary().as_html(), header=0, index_col=0)[1].iloc[1][0]
    beta = pd.read_html(results.summary().as_html(), header=0, index_col=0)[1].iloc[0][0]
    final_output[company] = [alpha, beta]
    alpha_list.append(alpha)
    beta_list.append(beta)

#convert dict to DataFrame
final_output_df= pd.DataFrame.from_dict(final_output).T
final_output_df.columns = ['alpha',' beta']
final_output_df  

  
  
  
  
  
  
  
  
  
  
  
  