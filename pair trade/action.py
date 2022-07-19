class pairTradeAction():
    def __init__(self, init, actionType):
        """_summary_

        Args:
            A_PriceList (list): A交易對價格變化歷程
            B_PriceList (list): B交易對價格變化歷程
            A_positionList (list): A交易對部位變化歷程
            B_positionList (list): B交易對部位變化歷程
            A_assetList (list): A交易對未實現損益變化歷程
            B_assetList (list): B交易對未實現損益變化歷程
            totalAssetList (list): portfolio未實現損益變化歷程
            availableList (list): 可用資金變化歷程
            A_EntryPrice (float): 紀錄A交易對進場價格
            B_EntryPrice (float): 紀錄B交易對進場價格
            entryPortfolio (float): 進場資產
            entryDate (ts): 進場時間
            init (float): 初始本金          
            AlongEntry (list): A交易對做多點位歷程
            AshortEntry (list): A交易對做空點位歷程
            AlongExit (list): A交易對平多點位歷程
            AshortExit (list): A交易對憑空點位歷程
            stopLossFlag (boolean):非訊號停損停利出場, 0:訊號出場, 1:停損停利出場
        """
        self.A_PriceList = []
        self.B_PriceList = []
        self.A_positionList = []
        self.B_positionList = []
        self.A_assetList = [] 
        self.B_assetList = []
        self.totalAssetList = []
        self.availableList = []
        self.A_EntryPrice = 0
        self.B_EntryPrice = 0
        self.entryPortfolio = 0
        self.entryDate = 0
        self.init = init
        self.AEntry = []
        self.AExit = []
        self.highTrailingEquity = 0
        self.stopLossFlag = False

        self.actionType = actionType
        self.strategy = {(0,1): self._forwardEntry, 
                        (0,2): self._exitForwardStoploss,
                        (0,-1): self._backwardEntry,
                        (0,-2): self._exitBackwardStoploss,
                        (1,0): self._backwardExit,
                        (1,2): self._entryForwardStoploss, 
                        (1,-1): self._exitBackwardEntry, 
                        (1,-2): self._entryBackwardStoploss2, 
                        (2,0) : self._stoplossBackwardExit,
                        (2,1) : self._stoplossBackwardEntry, 
                        (2,-1) : self._stoplossBackwardEntry2, 
                        (2,-2) : self._stoplossBackward, 
                        (-1,0) : self._forwardExit, 
                        (-1,1) : self._exitForwardEntry, 
                        (-1,2) : self._entryForwardStoploss2, 
                        (-1,-2) : self._entryBackwardStoploss, 
                        (-2,0) : self._stoplossForwardExit, 
                        (-2,1) : self._stoplossForwardEntry2,
                        (-2,2) : self._stoplossForward, 
                        (-2,-1) : self._stoplossForwardEntry, } 

        self.stopLossDict = {
                             'fixedStoploss': self._fixedStoploss, 
                             'trailingStop': self._trailingStop,
                             'timeStop': self._timeStop
                             }  
    def stopLossHub(self):
        if self.stopLossType:
            self.stopLossDict[self.stopLossType]()
        else:
            self._record()

    def _fixedStoploss(self):
        AEquity = abs(self.A_positionList[-1]) * (self.A_Price - self.A_EntryPrice + self.A_EntryPrice) if self.A_positionList[-1] > 0 else abs(self.A_positionList[-1]) * (self.A_EntryPrice - self.A_Price + self.A_EntryPrice) if self.A_positionList[-1] < 0 else 0
        BEquity = abs(self.B_positionList[-1]) * (self.B_Price - self.B_EntryPrice + self.B_EntryPrice) if self.B_positionList[-1] > 0 else abs(self.B_positionList[-1]) * (self.B_EntryPrice - self.B_Price + self.B_EntryPrice) if self.B_positionList[-1] < 0 else 0
        currEquity = AEquity + BEquity
        pastEquity = self.entryPortfolio
        if self.fixedProfitTaking:
            if self.stopLossFlag == False and (currEquity - pastEquity)/pastEquity >  self.fixedProfitTaking:
                self._stoplossExit()
            else:
                self._record()
        elif self.fixedStoploss: 
            if self.stopLossFlag == False and (currEquity - pastEquity)/pastEquity < -self.fixedStoploss:
                self._stoplossExit()
            else:
                self._record()
        else:
            self._record()

    def _trailingStop(self):
        AEquity = abs(self.A_positionList[-1]) * (self.A_Price - self.A_EntryPrice + self.A_EntryPrice) if self.A_positionList[-1] > 0 else abs(self.A_positionList[-1]) * (self.A_EntryPrice - self.A_Price + self.A_EntryPrice) if self.A_positionList[-1] < 0 else 0
        BEquity = abs(self.B_positionList[-1]) * (self.B_Price - self.B_EntryPrice + self.B_EntryPrice) if self.B_positionList[-1] > 0 else abs(self.B_positionList[-1]) * (self.B_EntryPrice - self.B_Price + self.B_EntryPrice) if self.B_positionList[-1] < 0 else 0
        currEquity = AEquity + BEquity
        pastEquity = self.entryPortfolio
        self.highTrailingEquity = max(currEquity, pastEquity, self.highTrailingEquity)
        if self.trailingStoploss: 
            if self.stopLossFlag == False and currEquity < self.highTrailingEquity * (1-self.trailingStoploss):
                self._stoplossExit()
            else:
                self._record()
        elif self.trailingProfitTaking:
            if self.stopLossFlag == False and currEquity > self.highTrailingEquity * (1+self.trailingProfitTaking):
                self._stoplossExit()
            else:
                self._record()
        else:
            self._record()        

    def _timeStop(self):
        if (self.date - self.entryDate).days >= self.timeStop and self.stopLossFlag == False:
            self._stoplossExit()
        else:
            self._record()
    
    def _record(self):
        self.AEntry.append(0)
        self.AExit.append(0)
        self.A_PriceList.append(self.A_Price)
        self.B_PriceList.append(self.B_Price)
        self.A_positionList.append(self.A_positionList[-1] if len(self.A_positionList)>0 else 0)
        self.B_positionList.append(self.B_positionList[-1] if len(self.B_positionList)>0 else 0)
        self.A_assetList.append(abs(self.A_positionList[-1]) * (self.A_Price - self.A_EntryPrice + self.A_EntryPrice) if self.A_positionList[-1] > 0 else abs(self.A_positionList[-1]) * (self.A_EntryPrice - self.A_Price + self.A_EntryPrice) if self.A_positionList[-1] < 0 else 0)
        self.B_assetList.append(abs(self.B_positionList[-1]) * (self.B_Price - self.B_EntryPrice + self.B_EntryPrice) if self.B_positionList[-1] > 0 else abs(self.B_positionList[-1]) * (self.B_EntryPrice - self.B_Price + self.B_EntryPrice) if self.B_positionList[-1] < 0 else 0)
        self.totalAssetList.append( (self.A_assetList[-1] + self.B_assetList[-1]) if (self.A_assetList[-1] + self.B_assetList[-1]) != 0 else 0)
        if self.availableList:
            self.availableList.append(self.availableList[-1] if (self.A_assetList[-1] + self.B_assetList[-1]) == 0 else 0)
        else:
            self.availableList.append(self.init) 

    def _stoplossExit(self):   
        self.AEntry.append(0)
        self.AExit.append(1)
        self.A_PriceList.append(self.A_Price)
        self.B_PriceList.append(self.B_Price)
        ## 可用資金
        A_available = abs(self.A_positionList[-1]) * (self.A_Price - self.A_EntryPrice + self.A_EntryPrice) if self.A_positionList[-1] > 0 else abs(self.A_positionList[-1]) * (self.A_EntryPrice - self.A_Price + self.A_EntryPrice) if self.A_positionList[-1] < 0 else 0
        B_available = abs(self.B_positionList[-1]) * (self.B_Price - self.B_EntryPrice + self.B_EntryPrice) if self.B_positionList[-1] > 0 else abs(self.B_positionList[-1]) * (self.B_EntryPrice - self.B_Price + self.B_EntryPrice) if self.B_positionList[-1] < 0 else 0
        self.availableList.append(A_available + B_available)
        ## 部位資產
        self.A_assetList.append(0)
        self.B_assetList.append(0)
        self.totalAssetList.append(0)
        self.A_positionList.append(0)
        self.B_positionList.append(0)
        self.stopLossFlag = True
        # print('[Stop-loss point]', self.date) 
        
    def runAction(self, strategyKey, date, A_Price, B_Price, A_Side, B_Side, stopLossType , fixedProfitTaking, fixedStoploss, trailingProfitTaking, trailingStoploss, timeStop):
        """
        Args:
            strategyKey (tuple): pair status code.
            A_Price (float): price of symbol A.
            B_Price (float): price of symbol B.
            A_Side (float): side of symbol A.
            B_Side (float): side of symbol B.
            stopLossType (tuple): stopLoss type, stopLoss, trailingStop, timeStop.
            fixedProfitTaking (float): fixed Profit Taking point.
            fixedStoploss (float): fixed Stoploss point.
            trailingProfitTaking (float): trailing Profit Taking point.
            trailingStoploss (float): trailing Stoploss point.
            timeStop (int): time stop
        """
        self.strategyKey = strategyKey
        self.date = date
        self.A_Price = A_Price
        self.B_Price = B_Price
        self.A_Side = A_Side
        self.B_Side = B_Side
        self.stopLossType = stopLossType
        self.fixedProfitTaking = fixedProfitTaking
        self.fixedStoploss = fixedStoploss
        self.trailingProfitTaking = trailingProfitTaking
        self.trailingStoploss = trailingStoploss
        self.timeStop = timeStop

        if strategyKey not in self.strategy and (abs(strategyKey[0]) == 1 and abs(strategyKey[1]) == 1):
            self.stopLossHub()

        elif strategyKey not in self.strategy and (abs(strategyKey[0]) != 1 or abs(strategyKey[1]) != 1):
            self._record()

        else:
            self.strategy[strategyKey]()

        
    def _stoplossBackwardEntry2(self):
        """
        statusList = (2, -1)
        long B 
        short A  
        """
        self.AEntry.append(1)
        self.AExit.append(0)
        self.A_PriceList.append(self.A_Price)
        self.B_PriceList.append(self.B_Price)
        if self.actionType == 'amount':
            A_asset = self.availableList[-1]/2 if len(self.availableList) else self.init/2
            B_asset = self.availableList[-1]/2 if len(self.availableList) else self.init/2
            self.A_assetList.append(A_asset)
            self.B_assetList.append(B_asset)
            self.A_positionList.append(A_asset * self.A_Side/self.A_Price)
            self.B_positionList.append(B_asset * self.B_Side/self.B_Price)
            self.totalAssetList.append(A_asset + B_asset)
            self.availableList.append(0)
        elif self.actionType == 'unit':
            A_asset = self.availableList[-1]/(1+abs(self.B_Side)) if len(self.availableList) else self.init/(1+abs(self.B_Side))
            B_asset = A_asset * abs(self.B_Side)
            self.A_assetList.append(A_asset)
            self.B_assetList.append(B_asset) 
            self.A_positionList.append(A_asset * self.A_Side/self.A_Price)
            self.B_positionList.append(A_asset * self.B_Side/self.B_Price)
            self.totalAssetList.append(A_asset + B_asset)
            self.availableList.append(0)
        self.A_EntryPrice = self.A_Price
        self.B_EntryPrice = self.B_Price
        self.entryPortfolio = self.totalAssetList[-1]
        self.entryDate = self.date
        self.highTrailingEquity = 0
        
    def _stoplossForwardEntry2(self):
        """
        statusList = (-2, 1)
        long A 
        short B    
        """
        ### 出場
        self.AEntry.append(1)
        self.AExit.append(0)
        self.A_PriceList.append(self.A_Price)
        self.B_PriceList.append(self.B_Price)
        if self.actionType == 'amount':
            A_asset = self.availableList[-1]/2 if len(self.availableList) else self.init/2
            B_asset = self.availableList[-1]/2 if len(self.availableList) else self.init/2
            self.A_assetList.append(A_asset)
            self.B_assetList.append(B_asset)
            self.A_positionList.append(A_asset * self.A_Side/self.A_Price)
            self.B_positionList.append(B_asset * self.B_Side/self.B_Price)
            self.totalAssetList.append(A_asset + B_asset)
            self.availableList.append(0)
        elif self.actionType == 'unit':
            A_asset = self.availableList[-1]/(1+abs(self.B_Side)) if len(self.availableList) else self.init/(1+abs(self.B_Side))
            B_asset = A_asset * abs(self.B_Side)
            self.A_assetList.append(A_asset)
            self.B_assetList.append(B_asset) 
            self.A_positionList.append(A_asset * self.A_Side/self.A_Price)
            self.B_positionList.append(A_asset * self.B_Side/self.B_Price)
            self.totalAssetList.append(A_asset + B_asset)
            self.availableList.append(0)
        self.A_EntryPrice = self.A_Price
        self.B_EntryPrice = self.B_Price
        self.entryPortfolio = self.totalAssetList[-1]
        self.entryDate = self.date
        self.highTrailingEquity = 0

    def _stoplossBackwardEntry(self):
        """
        statusList = (2,1)
        long A 
        short B    
        """
        self.AEntry.append(1)
        self.AExit.append(0)
        self.A_PriceList.append(self.A_Price)
        self.B_PriceList.append(self.B_Price)
        if self.actionType == 'amount':
            A_asset = self.availableList[-1]/2 if len(self.availableList) else self.init/2
            B_asset = self.availableList[-1]/2 if len(self.availableList) else self.init/2
            self.A_assetList.append(A_asset)
            self.B_assetList.append(B_asset)
            self.A_positionList.append(A_asset * self.A_Side/self.A_Price)
            self.B_positionList.append(B_asset * self.B_Side/self.B_Price)
            self.totalAssetList.append(A_asset + B_asset)
            self.availableList.append(0)
        elif self.actionType == 'unit':
            A_asset = self.availableList[-1]/(1+abs(self.B_Side)) if len(self.availableList) else self.init/(1+abs(self.B_Side))
            B_asset = A_asset * abs(self.B_Side)
            self.A_assetList.append(A_asset)
            self.B_assetList.append(B_asset) 
            self.A_positionList.append(A_asset * self.A_Side/self.A_Price)
            self.B_positionList.append(A_asset * self.B_Side/self.B_Price)
            self.totalAssetList.append(A_asset + B_asset)
            self.availableList.append(0)
        self.A_EntryPrice = self.A_Price
        self.B_EntryPrice = self.B_Price
        self.entryPortfolio = self.totalAssetList[-1]
        self.entryDate = self.date
        self.highTrailingEquity = 0

    def _stoplossForwardEntry(self):
        """
        statusList = (-2,-1)
        long B 
        short A    
        """
        self.AEntry.append(1)
        self.AExit.append(0)
        self.A_PriceList.append(self.A_Price)
        self.B_PriceList.append(self.B_Price)
        if self.actionType == 'amount':
            A_asset = self.availableList[-1]/2 if len(self.availableList) else self.init/2
            B_asset = self.availableList[-1]/2 if len(self.availableList) else self.init/2
            self.A_assetList.append(A_asset)
            self.B_assetList.append(B_asset)
            self.A_positionList.append(A_asset * self.A_Side/self.A_Price)
            self.B_positionList.append(B_asset * self.B_Side/self.B_Price)
            self.totalAssetList.append(A_asset + B_asset)
            self.availableList.append(0)
        elif self.actionType == 'unit':
            A_asset = self.availableList[-1]/(1+abs(self.B_Side)) if len(self.availableList) else self.init/(1+abs(self.B_Side))
            B_asset = A_asset * abs(self.B_Side)
            self.A_assetList.append(A_asset)
            self.B_assetList.append(B_asset) 
            self.A_positionList.append(A_asset * self.A_Side/self.A_Price)
            self.B_positionList.append(A_asset * self.B_Side/self.B_Price)
            self.totalAssetList.append(A_asset + B_asset)
            self.availableList.append(0)
        self.A_EntryPrice = self.A_Price
        self.B_EntryPrice = self.B_Price
        self.entryPortfolio = self.totalAssetList[-1]
        self.entryDate = self.date
        self.highTrailingEquity = 0
        
    def _entryForwardStoploss(self):
        """
        statusList = (1, 2)
        long A 
        short B
        close the position
        """
        if self.stopLossFlag:
            self._record()
            self.stopLossFlag = False
        else:
            self.AEntry.append(0)
            self.AExit.append(1)
            self.A_PriceList.append(self.A_Price)
            self.B_PriceList.append(self.B_Price)
            ## 可用資金
            A_available = abs(self.A_positionList[-1]) * (self.A_Price - self.A_EntryPrice + self.A_EntryPrice) if self.A_positionList[-1] > 0 else abs(self.A_positionList[-1]) * (self.A_EntryPrice - self.A_Price + self.A_EntryPrice) if self.A_positionList[-1] < 0 else 0
            B_available = abs(self.B_positionList[-1]) * (self.B_Price - self.B_EntryPrice + self.B_EntryPrice) if self.B_positionList[-1] > 0 else abs(self.B_positionList[-1]) * (self.B_EntryPrice - self.B_Price + self.B_EntryPrice) if self.B_positionList[-1] < 0 else 0
            self.availableList.append(A_available + B_available)
            ## 部位資產
            self.A_assetList.append(0)
            self.B_assetList.append(0)
            self.totalAssetList.append(0)
            self.A_positionList.append(0)
            self.B_positionList.append(0)

    def _entryBackwardStoploss2(self):
        """
        statusList = (1, -2)
        long A 
        short B
        close the position
        """
        if self.stopLossFlag:
            self._record()
            self.stopLossFlag = False
        else:
            self.AEntry.append(0)
            self.AExit.append(1)
            self.A_PriceList.append(self.A_Price)
            self.B_PriceList.append(self.B_Price)
            ## 可用資金
            A_available = abs(self.A_positionList[-1]) * (self.A_Price - self.A_EntryPrice + self.A_EntryPrice) if self.A_positionList[-1] > 0 else abs(self.A_positionList[-1]) * (self.A_EntryPrice - self.A_Price + self.A_EntryPrice) if self.A_positionList[-1] < 0 else 0
            B_available = abs(self.B_positionList[-1]) * (self.B_Price - self.B_EntryPrice + self.B_EntryPrice) if self.B_positionList[-1] > 0 else abs(self.B_positionList[-1]) * (self.B_EntryPrice - self.B_Price + self.B_EntryPrice) if self.B_positionList[-1] < 0 else 0
            self.availableList.append(A_available + B_available)
            ## 部位資產
            self.A_assetList.append(0)
            self.B_assetList.append(0)
            self.totalAssetList.append(0)
            self.A_positionList.append(0)
            self.B_positionList.append(0)
        
    def _entryBackwardStoploss(self):
        """
        statusList = (-1,-2)
        long B 
        short A
        close the position  
        """
        if self.stopLossFlag:
            self._record()
            self.stopLossFlag = False
        else:
            self.AEntry.append(0)
            self.AExit.append(1)
            self.A_PriceList.append(self.A_Price)
            self.B_PriceList.append(self.B_Price)
            ## 可用資金
            A_available = abs(self.A_positionList[-1]) * (self.A_Price - self.A_EntryPrice + self.A_EntryPrice) if self.A_positionList[-1] > 0 else abs(self.A_positionList[-1]) * (self.A_EntryPrice - self.A_Price + self.A_EntryPrice) if self.A_positionList[-1] < 0 else 0
            B_available = abs(self.B_positionList[-1]) * (self.B_Price - self.B_EntryPrice + self.B_EntryPrice) if self.B_positionList[-1] > 0 else abs(self.B_positionList[-1]) * (self.B_EntryPrice - self.B_Price + self.B_EntryPrice) if self.B_positionList[-1] < 0 else 0
            self.availableList.append(A_available + B_available)
            ## 部位資產
            self.A_assetList.append(0)
            self.B_assetList.append(0)
            self.totalAssetList.append(0)
            self.A_positionList.append(0)
            self.B_positionList.append(0)
        
    def _entryForwardStoploss2(self):
        """
        statusList = (-1,2)
        long B 
        short A
        close the position  
        """
        if self.stopLossFlag:
            self._record()
            self.stopLossFlag = False
        else:
            self.AEntry.append(0)
            self.AExit.append(1)
            self.A_PriceList.append(self.A_Price)
            self.B_PriceList.append(self.B_Price)
            ## 可用資金
            A_available = abs(self.A_positionList[-1]) * (self.A_Price - self.A_EntryPrice + self.A_EntryPrice) if self.A_positionList[-1] > 0 else abs(self.A_positionList[-1]) * (self.A_EntryPrice - self.A_Price + self.A_EntryPrice) if self.A_positionList[-1] < 0 else 0
            B_available = abs(self.B_positionList[-1]) * (self.B_Price - self.B_EntryPrice + self.B_EntryPrice) if self.B_positionList[-1] > 0 else abs(self.B_positionList[-1]) * (self.B_EntryPrice - self.B_Price + self.B_EntryPrice) if self.B_positionList[-1] < 0 else 0
            self.availableList.append(A_available + B_available)
            ## 部位資產
            self.A_assetList.append(0)
            self.B_assetList.append(0)
            self.totalAssetList.append(0)
            self.A_positionList.append(0)
            self.B_positionList.append(0)

    def _forwardEntry(self):
        """
        statusList = (0,1)
        """
        self.AEntry.append(1)
        self.AExit.append(0)
        self.A_PriceList.append(self.A_Price)
        self.B_PriceList.append(self.B_Price)
        if self.actionType == 'amount':
            A_asset = self.availableList[-1]/2 if len(self.availableList) else self.init/2
            B_asset = self.availableList[-1]/2 if len(self.availableList) else self.init/2
            self.A_assetList.append(A_asset)
            self.B_assetList.append(B_asset)
            self.A_positionList.append(A_asset * self.A_Side/self.A_Price)
            self.B_positionList.append(B_asset * self.B_Side/self.B_Price)
            self.totalAssetList.append(A_asset + B_asset)
            self.availableList.append(0)
        elif self.actionType == 'unit':
            A_asset = self.availableList[-1]/(1+abs(self.B_Side)) if len(self.availableList) else self.init/(1+abs(self.B_Side))
            B_asset = A_asset * abs(self.B_Side)
            self.A_assetList.append(A_asset)
            self.B_assetList.append(B_asset) 
            self.A_positionList.append(A_asset * self.A_Side/self.A_Price)
            self.B_positionList.append(A_asset * self.B_Side/self.B_Price)
            self.totalAssetList.append(A_asset + B_asset)
            self.availableList.append(0)
        self.A_EntryPrice = self.A_Price
        self.B_EntryPrice = self.B_Price
        self.entryPortfolio = self.totalAssetList[-1]
        self.entryDate = self.date
        self.highTrailingEquity = 0
            
    def _backwardEntry(self):
        """
        statusList = (0,-1)
        A:long
        B:short
        """
        self.AEntry.append(1)
        self.AExit.append(0)
        self.A_PriceList.append(self.A_Price)
        self.B_PriceList.append(self.B_Price)
        if self.actionType == 'amount':
            A_asset = self.availableList[-1]/2 if len(self.availableList) else self.init/2
            B_asset = self.availableList[-1]/2 if len(self.availableList) else self.init/2
            self.A_assetList.append(A_asset)
            self.B_assetList.append(B_asset)
            self.A_positionList.append(A_asset * self.A_Side/self.A_Price)
            self.B_positionList.append(B_asset * self.B_Side/self.B_Price)
            self.totalAssetList.append(A_asset + B_asset)
            self.availableList.append(0)
        elif self.actionType == 'unit':
            A_asset = self.availableList[-1]/(1+abs(self.B_Side)) if len(self.availableList) else self.init/(1+abs(self.B_Side))
            B_asset = A_asset * abs(self.B_Side)
            self.A_assetList.append(A_asset)
            self.B_assetList.append(B_asset) 
            self.A_positionList.append(A_asset * self.A_Side/self.A_Price)
            self.B_positionList.append(A_asset * self.B_Side/self.B_Price)
            self.totalAssetList.append(A_asset + B_asset)
            self.availableList.append(0)
        self.A_EntryPrice = self.A_Price
        self.B_EntryPrice = self.B_Price
        self.entryPortfolio = self.totalAssetList[-1]
        self.entryDate = self.date
        self.highTrailingEquity = 0


    def _backwardExit(self):
        """
        statusList = (1,0)
        long A
        short B
        close the position
        """
        if self.stopLossFlag:
            self._record()
            self.stopLossFlag = False
        else:
            self.AEntry.append(0)
            self.AExit.append(1)
            self.A_PriceList.append(self.A_Price)
            self.B_PriceList.append(self.B_Price)
            ## 可用資金
            A_available = abs(self.A_positionList[-1]) * (self.A_Price - self.A_EntryPrice + self.A_EntryPrice) if self.A_positionList[-1] > 0 else abs(self.A_positionList[-1]) * (self.A_EntryPrice - self.A_Price + self.A_EntryPrice) if self.A_positionList[-1] < 0 else 0
            B_available = abs(self.B_positionList[-1]) * (self.B_Price - self.B_EntryPrice + self.B_EntryPrice) if self.B_positionList[-1] > 0 else abs(self.B_positionList[-1]) * (self.B_EntryPrice - self.B_Price + self.B_EntryPrice) if self.B_positionList[-1] < 0 else 0
            self.availableList.append(A_available + B_available)
            ## 部位資產
            self.A_assetList.append(0)
            self.B_assetList.append(0)
            self.totalAssetList.append(0)
            self.A_positionList.append(0)
            self.B_positionList.append(0)

        
    def _exitBackwardEntry(self):
        """
        statusList = (1,-1)
        long A
        short B
        close the position
        long B 
        short A
        """
        if self.stopLossFlag:
            self.AEntry.append(1)
            self.AExit.append(0)
            self.A_PriceList.append(self.A_Price)
            self.B_PriceList.append(self.B_Price)
            if self.actionType == 'amount':
                A_asset = self.availableList[-1]/2 if len(self.availableList) else self.init/2
                B_asset = self.availableList[-1]/2 if len(self.availableList) else self.init/2
                self.A_assetList.append(A_asset)
                self.B_assetList.append(B_asset)
                self.A_positionList.append(A_asset * self.A_Side/self.A_Price)
                self.B_positionList.append(B_asset * self.B_Side/self.B_Price)
                self.totalAssetList.append(A_asset + B_asset)
                self.availableList.append(0)
            elif self.actionType == 'unit':
                A_asset = self.availableList[-1]/(1+abs(self.B_Side)) if len(self.availableList) else self.init/(1+abs(self.B_Side))
                B_asset = A_asset * abs(self.B_Side)
                self.A_assetList.append(A_asset)
                self.B_assetList.append(B_asset) 
                self.A_positionList.append(A_asset * self.A_Side/self.A_Price)
                self.B_positionList.append(A_asset * self.B_Side/self.B_Price)
                self.totalAssetList.append(A_asset + B_asset)
                self.availableList.append(0)
            self.A_EntryPrice = self.A_Price
            self.B_EntryPrice = self.B_Price
            self.entryPortfolio = self.totalAssetList[-1]
            self.entryDate = self.date
            self.stopLossFlag = False
        else:
            self.AEntry.append(1)
            self.AExit.append(0)
            ### 出場
            self.A_PriceList.append(self.A_Price)
            self.B_PriceList.append(self.B_Price)
            ## 可用資金
            A_available = abs(self.A_positionList[-1]) * (self.A_Price - self.A_EntryPrice + self.A_EntryPrice) if self.A_positionList[-1] > 0 else abs(self.A_positionList[-1]) * (self.A_EntryPrice - self.A_Price + self.A_EntryPrice) if self.A_positionList[-1] < 0 else 0
            B_available = abs(self.B_positionList[-1]) * (self.B_Price - self.B_EntryPrice + self.B_EntryPrice) if self.B_positionList[-1] > 0 else abs(self.B_positionList[-1]) * (self.B_EntryPrice - self.B_Price + self.B_EntryPrice) if self.B_positionList[-1] < 0 else 0
            available = A_available +B_available
            
            ### 進場
            if self.actionType == 'amount':
                A_asset = available/2
                B_asset = available/2
                self.A_assetList.append(A_asset)
                self.B_assetList.append(B_asset)
                self.A_positionList.append(A_asset * self.A_Side/self.A_Price)
                self.B_positionList.append(B_asset * self.B_Side/self.B_Price)
                self.totalAssetList.append(A_asset + B_asset)
                self.availableList.append(0)
            elif self.actionType == 'unit':
                A_asset = self.availableList[-1]/(1+abs(self.B_Side)) 
                B_asset = A_asset * abs(self.B_Side)
                self.A_assetList.append(A_asset)
                self.B_assetList.append(B_asset) 
                self.A_positionList.append(A_asset * self.A_Side/self.A_Price)
                self.B_positionList.append(A_asset * self.B_Side/self.B_Price)
                self.totalAssetList.append(A_asset + B_asset)
                self.availableList.append(0)
            self.A_EntryPrice = self.A_Price
            self.B_EntryPrice = self.B_Price
            self.entryPortfolio = self.totalAssetList[-1]
            self.entryDate = self.date
        self.highTrailingEquity = 0
        
    def _forwardExit(self):
        """
        statusList = (-1,0)
        long B
        short A
        close the position
        """
        if self.stopLossFlag:
            self._record()
            self.stopLossFlag = False
        else:
            self.AEntry.append(0)
            self.AExit.append(1)
            self.A_PriceList.append(self.A_Price)
            self.B_PriceList.append(self.B_Price)
            ## 可用資金
            A_available = abs(self.A_positionList[-1]) * (self.A_Price - self.A_EntryPrice + self.A_EntryPrice) if self.A_positionList[-1] > 0 else abs(self.A_positionList[-1]) * (self.A_EntryPrice - self.A_Price + self.A_EntryPrice) if self.A_positionList[-1] < 0 else 0
            B_available = abs(self.B_positionList[-1]) * (self.B_Price - self.B_EntryPrice + self.B_EntryPrice) if self.B_positionList[-1] > 0 else abs(self.B_positionList[-1]) * (self.B_EntryPrice - self.B_Price + self.B_EntryPrice) if self.B_positionList[-1] < 0 else 0
            self.availableList.append(A_available + B_available)
            ## 部位資產
            self.A_assetList.append(0)
            self.B_assetList.append(0)
            self.totalAssetList.append(0)
            self.A_positionList.append(0)
            self.B_positionList.append(0)
        
    def _exitForwardEntry(self):
        """
        statusList = (-1,1)
        long B
        short A
        close the position
        long A
        short B
        """
        if self.stopLossFlag:
            self.AEntry.append(1)
            self.AExit.append(0)
            self.A_PriceList.append(self.A_Price)
            self.B_PriceList.append(self.B_Price)
            if self.actionType == 'amount':
                A_asset = self.availableList[-1]/2 if len(self.availableList) else self.init/2
                B_asset = self.availableList[-1]/2 if len(self.availableList) else self.init/2
                self.A_assetList.append(A_asset)
                self.B_assetList.append(B_asset)
                self.A_positionList.append(A_asset * self.A_Side/self.A_Price)
                self.B_positionList.append(B_asset * self.B_Side/self.B_Price)
                self.totalAssetList.append(A_asset + B_asset)
                self.availableList.append(0)
            elif self.actionType == 'unit':
                A_asset = self.availableList[-1]/(1+abs(self.B_Side)) if len(self.availableList) else self.init/(1+abs(self.B_Side))
                B_asset = A_asset * abs(self.B_Side)
                self.A_assetList.append(A_asset)
                self.B_assetList.append(B_asset) 
                self.A_positionList.append(A_asset * self.A_Side/self.A_Price)
                self.B_positionList.append(A_asset * self.B_Side/self.B_Price)
                self.totalAssetList.append(A_asset + B_asset)
                self.availableList.append(0)
            self.A_EntryPrice = self.A_Price
            self.B_EntryPrice = self.B_Price
            self.entryPortfolio = self.totalAssetList[-1]
            self.entryDate = self.date
            self.stopLossFlag = False
        else:
            self.AEntry.append(1)
            self.AExit.append(0)
            ### 出場
            self.A_PriceList.append(self.A_Price)
            self.B_PriceList.append(self.B_Price)
            ## 可用資金
            A_available = abs(self.A_positionList[-1]) * (self.A_Price - self.A_EntryPrice + self.A_EntryPrice) if self.A_positionList[-1] > 0 else abs(self.A_positionList[-1]) * (self.A_EntryPrice - self.A_Price + self.A_EntryPrice) if self.A_positionList[-1] < 0 else 0
            B_available = abs(self.B_positionList[-1]) * (self.B_Price - self.B_EntryPrice + self.B_EntryPrice) if self.B_positionList[-1] > 0 else abs(self.B_positionList[-1]) * (self.B_EntryPrice - self.B_Price + self.B_EntryPrice) if self.B_positionList[-1] < 0 else 0
            available = A_available +B_available
            
            ### 進場
            if self.actionType == 'amount':
                A_asset = available/2
                B_asset = available/2
                self.A_assetList.append(A_asset)
                self.B_assetList.append(B_asset)
                self.A_positionList.append(A_asset * self.A_Side/self.A_Price)
                self.B_positionList.append(B_asset * self.B_Side/self.B_Price)
                self.totalAssetList.append(A_asset + B_asset)
                self.availableList.append(0)
            elif self.actionType == 'unit':
                A_asset = self.availableList[-1]/(1+abs(self.B_Side)) 
                B_asset = A_asset * abs(self.B_Side)
                self.A_assetList.append(A_asset)
                self.B_assetList.append(B_asset) 
                self.A_positionList.append(A_asset * self.A_Side/self.A_Price)
                self.B_positionList.append(A_asset * self.B_Side/self.B_Price)
                self.totalAssetList.append(A_asset + B_asset)
                self.availableList.append(0)
            self.A_EntryPrice = self.A_Price
            self.B_EntryPrice = self.B_Price
            self.entryPortfolio = self.totalAssetList[-1]
            self.entryDate = self.date
        self.highTrailingEquity = 0
        
    def _exitForwardStoploss(self):
        """
        出場點 -> 正指損點 --不動作
        statusList = (0,2)
        """
        self._record()

    def _exitBackwardStoploss(self):
        """
        出場點 -> 負指損點 --不動作
        statusList = (0,-2)
        """
        self._record()
            
    def _stoplossBackwardExit(self):
        """
        正指損點 -> 出場點 --不動作
        statusList = (2, 0)
        """
        self._record()

    def _stoplossForwardExit(self):
        """
        負指損點 -> 出場點 --不動作
        statusList = (-2, 0)
        """
        self._record()

    def _stoplossForward(self):
        """
        負指損點 -> 正指損點 --不動作
        statusList = (-2, 2)
        """
        self._record()

    def _stoplossBackward(self):
        """
        正指損點 -> 負指損點 --不動作
        statusList = (2, -2)
        """
        self._record()