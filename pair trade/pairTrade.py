import pandas as pd
import numpy as np
import statsmodels.formula.api as sm
from numpy_ext import rolling_apply
import warnings
from action import pairTradeAction
from matplotlib import pyplot as plt
pd.set_option('display.float_format', lambda x: '%.8f' % x)
warnings.filterwarnings('ignore')

class pairTrade():
    def __init__(self, df):
        
        """
        Args:
            df (dataframe): input data, column = data, ASymbol, Bsymbol. 
            A_Symbol (string): A symbol name.
            B_Symbol (string): B symbol name.
            tradeTypeDict (dict): trade type setting.
            tradeType (string): spread, ratio, returnSpread, regression.  
        """        
        self.df = df
        self.A_Symbol = df.columns[0]
        self.B_Symbol = df.columns[1]
        self.tradeTypeDict = {
            'priceSpread': self._indicatorSpread, 
            'priceRatio': self._indicatorRatio, 
            'returnSpread': self._indicatorReturnSpread,
            'priceRegression': self._indicatorRegression
        }
        self.KPI = pd.DataFrame()
    
    def indicator(self, tradeType, rolling = 20):
        """
        不同trade的Z-score
        Z-score大於entry, 空A交易對, 多B交易對;Z-score小於entry, 多A交易對, 空B交易對
        
        Args:
            tradeType (string): spread, ratio, returnSpread, regression.        
        """
        self.rolling = rolling
        self.tradeType = tradeType
        self.tradeTypeDict[self.tradeType]()
        
        
    def _zScore(self, yport):
        zscore = (yport[-1]  - yport.mean()) / yport.std()
        return zscore
    
    def _indicatorSpread(self):
        """
        等金額下注
        """
        self.df['priceSpread'] = self.df.loc[:,self.A_Symbol] - self.df.loc[:,self.B_Symbol]
        self.df['zscore'] = rolling_apply(self._zScore, self.rolling, self.df['priceSpread'])
        self.df['zscore'] = self.df['zscore'].shift(1)
        # self.df['ASymbolSide'] = [-1 if i >= self.exit else 1 if i < -self.exit else 0 for i in self.df['zscore'].tolist()]
        
    def _indicatorRatio(self):
        """
        等金額下注
        """
        self.df['priceRatio'] = self.df.loc[:,self.A_Symbol]/self.df.loc[:,self.B_Symbol]
        self.df['zscore'] = rolling_apply(self._zScore, self.rolling,self.df.loc[:,'priceRatio'])
        self.df['zscore'] = self.df['zscore'].shift(1)
        # self.df['ASymbolSide'] = [-1 if i >= self.exit else 1 if i < -self.exit else 0 for i in self.df['zscore'].tolist()]

    def _indicatorReturnSpread(self):
        """
        等金額下注
        """
        self.df['A_return'] = self.df.loc[:,self.A_Symbol].pct_change()
        self.df['B_return'] = self.df.loc[:,self.B_Symbol].pct_change()
        self.df['returnSpread'] = self.df.loc[:,'A_return'] - self.df.loc[:,'B_return']
        self.df['zscore'] = rolling_apply(self._zScore, self.rolling, self.df.loc[:,'returnSpread'])
        self.df['zscore'] = self.df['zscore'].shift(1)
        # self.df['ASymbolSide'] = [-1 if i >= self.exit else 1 if i < -self.exit else 0 for i in self.df['zscore'].tolist()]

    def _indicatorRegression(self):
        """
        比例下注
        """
        hedgeRatio=np.full(self.df.shape[0], 0.0)
        for t in np.arange(self.rolling, len(hedgeRatio)):
            regress_results=sm.ols(formula="{} ~ {}".format(self.A_Symbol, self.B_Symbol), data=self.df[(t-self.rolling):t]).fit() # Note this can deal with NaN in top row
            hedgeRatio[t-1]=regress_results.params[1] ## beta1
        self.df['hedgeRatio'] = hedgeRatio 
        self.df['priceRegression'] = self.df.loc[:,self.A_Symbol] - self.df.loc[:,'hedgeRatio'] * self.df.loc[:,self.B_Symbol]
        self.df['zscore'] = rolling_apply(self._zScore, self.rolling, self.df.loc[:,'priceRegression'])
        self.df['zscore'] = self.df['zscore'].shift(1)
        # self.df['ASymbolSide'] = [-1 if i >= self.exit else 1 if i < -self.exit else 0 for i in self.df['zscore'].tolist()]
        
    def strategy(self, strategyType, actionType, entry, exit, signalStopLoss = None, stopLossType = None, init = 100000, fixedProfitTaking = None, fixedStoploss = None, trailingProfitTaking = None, trailingStoploss = None, timeStop = None):
        """
        Args:
            strategyType (string): divergence convergence.
            actionType (string): amount unit.
            entry (float): zscore entry point. 
            exit (float): zscore entry point. 
            singalStopLoss (float): singalStopLoss. 
            init (int, optional): initial amount. Defaults to 100000.
            stopLossType (tuple): stopLoss type, stopLoss, trailingStop, timeStop.
            stopLossPara (tuple): stopLoss parameter.
        """
        self.strategyType = strategyType
        self.actionType = actionType
        self.entry = entry
        self.exit = exit
        self.signalStopLoss = signalStopLoss
        self.stopLossType = stopLossType
        self.fixedProfitTaking = fixedProfitTaking
        self.fixedStoploss = fixedStoploss
        self.trailingProfitTaking = trailingProfitTaking
        self.trailingStoploss = trailingStoploss
        self.timeStop = timeStop
        self.init = init

        actionObject = pairTradeAction(self.init, self.actionType)
        
        pastStatus = 0
        date, statusList =  [], []
        
        if self.strategyType == "convergence":
            self.df['ASymbolSide'] = [-1 if i >= self.exit else 1 if i < -self.exit else 0 for i in self.df['zscore'].tolist()]
            self.df['BSymbolSide'] = self.df['hedgeRatio'] * self.df['ASymbolSide'] * -1 if 'hedgeRatio' in self.df.columns else self.df['ASymbolSide'] * -1
        elif self.strategyType == "divergence":
            self.df['ASymbolSide'] = [1 if i >= self.exit else -1 if i < -self.exit else 0 for i in self.df['zscore'].tolist()]
            self.df['BSymbolSide'] = self.df['hedgeRatio'] * self.df['ASymbolSide'] * -1 if 'hedgeRatio' in self.df.columns else self.df['ASymbolSide'] * -1
        else:
            raise Exception('strategyType must be divergence or convergence')

        for index, row in self.df.iterrows():
            if self.signalStopLoss:
                currStatus = 0 if (pastStatus == 1 and row['zscore'] < -self.exit) or (pastStatus == -1 and row['zscore'] > self.exit) else 1 if (pastStatus == 1 and row['zscore'] > self.exit or row['zscore'] > self.entry) and row['zscore'] < self.signalStopLoss else 2 if row['zscore'] > self.signalStopLoss else -1 if (pastStatus == -1 and row['zscore'] < -self.exit or row['zscore'] < -self.entry) and row['zscore'] > -self.signalStopLoss else -2 if row['zscore'] < -self.signalStopLoss else 0
            else:
                currStatus = 0 if (pastStatus == 1 and row['zscore'] < -self.exit) or (pastStatus == -1 and row['zscore'] > self.exit) else 1 if (pastStatus == 1 and row['zscore'] > self.exit or row['zscore'] > self.entry) else -1 if (pastStatus == -1 and row['zscore'] < -self.exit or row['zscore'] < -self.entry) else 0
            
            conStatus = (pastStatus, currStatus)
            pastStatus = currStatus
            actionObject.runAction(
                 strategyKey = conStatus,
                 date = index,
                 A_Price = row[self.A_Symbol],
                 B_Price = row[self.B_Symbol],
                 A_Side = row['ASymbolSide'],
                 B_Side = row['BSymbolSide'], 
                 stopLossType = self.stopLossType,
                 fixedProfitTaking = self.fixedProfitTaking, 
                 fixedStoploss = self.fixedStoploss, 
                 trailingProfitTaking = self.trailingProfitTaking, 
                 trailingStoploss = self.trailingStoploss, 
                 timeStop = self.timeStop

                 )
            # print(index, conStatus)
            date.append(index)
            statusList.append(currStatus)

        self.df['status'] = statusList
        self.df['A_position'] = actionObject.A_positionList
        self.df['B_position'] = actionObject.B_positionList
        self.df['A_asset'] = actionObject.A_assetList
        self.df['B_asset'] = actionObject.B_assetList
        self.df['totalAsset'] = actionObject.totalAssetList
        self.df['available'] = actionObject.availableList
        self.df['total'] = self.df['totalAsset'] + self.df['available']
        self.df['PNL'] = self.df['totalAsset'] + self.df['available'] - self.init
        self.df['AEntry'] = actionObject.AEntry
        self.df['AExit'] = actionObject.AExit
        DD = []
        initEquity = 100000
        for i in self.df['total'].tolist():
            initEquity = max(initEquity, i)
            DD.append(i - initEquity)
        self.df['DD'] = DD
            

        pastAsset = 0
        entryDate, AEntryPrice, AEntryPosition, AEntryAsset, BEntryPrice, BEntryPosition, BEntryAsset, totalEntryAsset= [], [], [], [], [], [], [], []
        exitDate,  AExitPrice, AExitPosition, AExitAsset, BExitPrice, BExitPosition, BExitAsset, totalExitAsset= [], [], [], [], [], [], [], []
        for index, row in self.df.iterrows():
            if row['A_position'] != pastAsset and pastAsset == 0:
                entryDate.append(index)
                AEntryPrice.append(row[self.A_Symbol]), AEntryPosition.append(row['A_position']), AEntryAsset.append(row['A_asset'])
                BEntryPrice.append(row[self.B_Symbol]), BEntryPosition.append(row['B_position']), BEntryAsset.append(row['B_asset'])
                totalEntryAsset.append(row['A_asset'] + row['B_asset'])
            elif row['A_position'] != pastAsset and pastAsset != 0:
                exitDate.append(index)
                AExitPrice.append(row[self.A_Symbol]), AExitPosition.append(AEntryPosition[-1])
                AAsset  = abs(AEntryPosition[-1]) * (row[self.A_Symbol] - AEntryPrice[-1] + AEntryPrice[-1]) if AEntryPosition[-1] > 0 else abs(AEntryPosition[-1]) * (AEntryPrice[-1] - row[self.A_Symbol] + AEntryPrice[-1])
                AExitAsset.append(AAsset)
                BExitPrice.append(row[self.B_Symbol]), BExitPosition.append(BEntryPosition[-1]) 
                BAsset  = abs(BEntryPosition[-1]) * (row[self.B_Symbol] - BEntryPrice[-1] + BEntryPrice[-1]) if BEntryPosition[-1] > 0 else abs(BEntryPosition[-1]) * (BEntryPrice[-1] - row[self.B_Symbol] + BEntryPrice[-1])
                BExitAsset.append(BAsset)
                totalExitAsset.append(row['available'])
            pastAsset = row['A_position']
        
        if len(entryDate) > len(exitDate):
            exitDate.append(self.df.index[-1])
            AExitPrice.append(self.df.loc[:, self.A_Symbol][-1])
            AExitPosition.append(AEntryPosition[-1])
            Aex = AEntryPosition[-1] * (self.df.loc[:, self.A_Symbol][-1] - AEntryPrice[-1] + AEntryPrice[-1]) if AEntryPosition[-1] > 0 else abs(AEntryPosition[-1]) * (AEntryPrice[-1] - self.df.loc[:, self.A_Symbol][-1] + AEntryPrice[-1]) 
            AExitAsset.append(Aex)
            BExitPrice.append(self.df.loc[:, self.B_Symbol][-1])
            BExitPosition.append(BEntryPosition[-1])
            Bex = BEntryPosition[-1] * (self.df.loc[:, self.B_Symbol][-1] - BEntryPrice[-1] + BEntryPrice[-1]) if BEntryPosition[-1] > 0 else abs(BEntryPosition[-1]) * (BEntryPrice[-1] - self.df.loc[:, self.B_Symbol][-1] + BEntryPrice[-1]) 
            BExitAsset.append(Bex)
            totalExitAsset.append(Aex + Bex)
            print("{}_{} 回測結果，場上有單已平倉".format(self.A_Symbol, self.B_Symbol))
        elif len(entryDate) - len(exitDate) > 1 or len(entryDate) != len(exitDate):
            raise Exception('check entry and exit point')
        else:
            print("{}_{} 回測結果".format(self.A_Symbol, self.B_Symbol))
            
        self.KPI['entryDate'] = entryDate
        self.KPI['AEntryPrice'] = AEntryPrice
        self.KPI['AEntryPosition'] = AEntryPosition
        self.KPI['AEntryAsset'] = AEntryAsset
        self.KPI['BEntryPrice'] = BEntryPrice
        self.KPI['BEntryPosition'] = BEntryPosition
        self.KPI['BEntryAsset'] = BEntryAsset
        self.KPI['totalEntryAsset'] = totalEntryAsset
        self.KPI['exitDate'] = exitDate
        self.KPI['AExitPrice'] = AExitPrice
        self.KPI['AExitPosition'] = AExitPosition
        self.KPI['AExitAsset'] = AExitAsset
        self.KPI['BExitPrice'] = BExitPrice
        self.KPI['BExitPosition'] = BExitPosition
        self.KPI['BExitAsset'] = BExitAsset
        self.KPI['totalExitAsset'] = totalExitAsset
        self.KPI['PNL'] = self.KPI['totalExitAsset'] - self.KPI['totalEntryAsset']

        win = [i for i in self.KPI['PNL'].tolist() if i > 0]
        loss = [i for i in self.KPI['PNL'].tolist() if i < 0]
        if win != 0 or loss !=0:
            Profit_Factor = sum(win)/abs(sum(loss))
            Win_Loss_Rate = (sum(win)/len(win))/(-sum(loss)/len(loss))

        MDD,Capital,MaxCapital = 0,0,0
        for p in self.KPI['PNL'].tolist():
            Capital += p
            MaxCapital = max(MaxCapital,Capital)
            DD = MaxCapital - Capital
            MDD = max(MDD,DD)

        print('-----------------------------{}-{}--------------------------'.format(self.A_Symbol, self.B_Symbol))
        print('初始價格', self.init)
        print('總損益: ', "{0:.8f}".format(sum(self.KPI['PNL'])))
        print('總交易次數: ', self.KPI.shape[0])
        print('平均損益: ', sum(self.KPI['PNL'])/self.KPI.shape[0])
        print('勝率: ', len(win)/self.KPI.shape[0])
        if win != 0 or loss !=0:
            print('獲利因子: ', Profit_Factor)
            print('賺賠比: ', Win_Loss_Rate)
        print('最大資金回落: ', MDD)
        print('夏普比率: ', np.mean(self.KPI['PNL'])/np.std(self.KPI['PNL']))
        print('年化報酬率: ', (1 + ((self.KPI['totalExitAsset'][self.KPI.shape[0]-1] - self.init)/self.init)) ** self.df.shape[0])

    def pplot(self):
        date = self.df.index

        Asym = self.df[self.A_Symbol]
        Bsym = self.df[self.B_Symbol]
        indicate = self.df[self.tradeType]
        total = self.df['total']
        zscore = self.df['zscore']
        A_position = self.df['A_position']
        B_position = self.df['B_position']
        drawdown = self.df['DD']

        fig, axs = plt.subplots(8, 1, sharex=True, figsize = (15, 10))
        fig.subplots_adjust(hspace=0)

        axs[0].plot(date, Asym, color = 'b')
        axs[0].set_ylabel("{}".format(self.A_Symbol))
        axs[0].scatter(
            self.df[self.df['AEntry'] == 1].index,
            self.df[self.df['AEntry'] == 1][self.A_Symbol],
            c = "g",
            s = 10
            )
        axs[0].scatter(
            self.df[self.df['AExit'] == 1].index,
            self.df[self.df['AExit'] == 1][self.A_Symbol],
            c = "r",
            s = 10
            )
        axs[1].plot(date, Bsym, color = 'b')
        axs[1].set_ylabel("{}".format(self.B_Symbol))
        axs[1].scatter(
            self.df[self.df['AEntry'] == 1].index,
            self.df[self.df['AEntry'] == 1][self.B_Symbol],
            c = "g",
            s = 10
            )
        axs[1].scatter(
            self.df[self.df['AExit'] == 1].index,
            self.df[self.df['AExit'] == 1][self.B_Symbol],
            c = "r",
            s = 10
            )
        axs[2].plot(date, indicate, color = 'b')
        axs[2].set_ylabel("{}".format(self.tradeType))
        axs[2].scatter(
            self.df[self.df['AEntry'] == 1].index,
            self.df[self.df['AEntry'] == 1][self.tradeType],
            c = "g",
            s = 10
            )
        axs[2].scatter(
            self.df[self.df['AExit'] == 1].index,
            self.df[self.df['AExit'] == 1][self.tradeType],
            c = "r",
            s = 10
            )
        axs[3].plot(date, total, color = 'b')
        axs[3].set_ylabel("equity curve")
        axs[3].scatter(
            self.df[self.df['AEntry'] == 1].index,
            self.df[self.df['AEntry'] == 1]['total'],
            c = "g",
            s = 10
            )
        axs[3].scatter(
            self.df[self.df['AExit'] == 1].index,
            self.df[self.df['AExit'] == 1]['total'],
            c = "r",
            s = 10
            )
        axs[4].plot(date, zscore, color = 'y')
        axs[4].set_ylabel("Z-score")
        axs[4].scatter(
            self.df[self.df['AEntry'] == 1].index,
            self.df[self.df['AEntry'] == 1]['zscore'],
            c = "g",
            s = 10
            )
        axs[4].scatter(
            self.df[self.df['AExit'] == 1].index,
            self.df[self.df['AExit'] == 1]['zscore'],
            c = "r",
            s = 10
            )
        # axs[4].set_yticks([-self.signalStopLoss, -self.entry, self.exit, -self.exit, self.entry, self.signalStopLoss])
        # axs[4].set_ylim(-3, 3)
        axs[5].plot(date, A_position, color = 'y')
        axs[5].set_ylabel("{}_position".format(self.A_Symbol))
        axs[5].scatter(
            self.df[self.df['AEntry'] == 1].index,
            self.df[self.df['AEntry'] == 1]['A_position'],
            c = "g",
            s = 10
            )
        axs[5].scatter(
            self.df[self.df['AExit'] == 1].index,
            self.df[self.df['AExit'] == 1]['A_position'],
            c = "r",
            s = 10
            )

        axs[6].plot(date, B_position, color = 'y')
        axs[6].set_ylabel("{}_position".format(self.B_Symbol))
        axs[6].scatter(
            self.df[self.df['AEntry'] == 1].index,
            self.df[self.df['AEntry'] == 1]['B_position'],
            c = "g",
            s = 10
            )
        axs[6].scatter(
            self.df[self.df['AExit'] == 1].index,
            self.df[self.df['AExit'] == 1]['B_position'],
            c = "r",
            s = 10
            )


        axs[7].plot(date, drawdown, color = 'y')
        axs[7].set_ylabel("{}".format('drawdown'))
        axs[7].scatter(
            self.df[self.df['AEntry'] == 1].index,
            self.df[self.df['AEntry'] == 1]['DD'],
            c = "g",
            s = 10
            )
        axs[7].scatter(
            self.df[self.df['AExit'] == 1].index,
            self.df[self.df['AExit'] == 1]['DD'],
            c = "r",
            s = 10
            )

        axs[0].grid()
        axs[1].grid()
        axs[2].grid()
        axs[3].grid()
        axs[4].grid()
        axs[5].grid()
        axs[6].grid()
        axs[7].grid()
        plt.show()