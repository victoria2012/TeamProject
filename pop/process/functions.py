

class functions:
        def d1(self):
            conn = sqlite3.connect('./db.sqlite3')
            c_select = conn.cursor()
            final = c_select.execute("SELECT * FROM article where stock != 'stock' order by date desc , time desc")
            df = pd.DataFrame(final)
            df.columns= ['id', 'date' , 'time' , 'title', 'press' ,'stock' , 'posi_nega' ]
            result = df  
            return result;