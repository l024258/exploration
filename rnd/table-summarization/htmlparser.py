import os
import lxml
from bs4 import BeautifulSoup
import pandas as pd

class Htmlparser:
    
    def __init__(self, path, filename):
        self.path = path
        self.filename = filename
        
    def setThePath(self):
        gwd = os.getcwd()+"/"+self.path
        return gwd
    
    def readHtmlFile(self):
        folderPath = self.setThePath() 
        filepath = folderPath+"/"+self.filename
        with open(filepath, 'r') as f:
            contents = f.read()
            soup = BeautifulSoup(contents, 'lxml')
        return soup
    
    def getDataFrame(self):
        soup = self.readHtmlFile()
        table = soup.find('table', attrs={'class':'subs noBorders evenRows'})
        table = soup.find_all('table')
        df = pd.read_html(str(table))[0]
        return df
    
       