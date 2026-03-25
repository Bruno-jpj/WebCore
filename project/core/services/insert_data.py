import mariadb
import sys
import random
import os

# QUESTO FILE SERVE PER AUTO-INSERIRE I DATI NELLA TABELLA MACCHINE (DATI SIMULATI) E NELLA TABELLA INFORMAZIONI (DATI UFFICIALI)
# QUESTO PROGRAMMA NON HA BISOGNO DEL SERVIZIO ONLINE 


# FUNZIONA TUTTO NON TOCCARE

class Run():
    def __init__(self):
        self.db_conf = {
            'host':'localhost',
            'port':3306,
            'user':'root',
            'password':'Qt352!dTf',
            'database':'macchine'
        }
        
        self.connection = None
        self.cursor = None
        
        self.macchine = None
        self.info = None
        
        try:
            print("Connecting to MariaDB...")
            self.connection = mariadb.connect(**self.db_conf)
            print("Connection successful!")
        except mariadb.Error as e:
            print(f"Errore connect: [{e}]")
            sys.exit(1)
        #
        self.cursor = self.connection.cursor()
        #
    #
    def select_alarms(self):
        try:
            self.cursor.execute("""select id, titolo from allarmi_soluzioni;""")
            self.alarms = self.cursor.fetchall()
            return self.alarms
        except Exception as e:
            print(f"Errore select-macchine: [{e}]")
            sys.exit(1)
    #
    def select_macchine(self):
        try:
            self.cursor.execute("""select id, piano_produzione from macchinari;""")
            self.macchine = self.cursor.fetchall()
            return self.macchine
        except Exception as e:
            print(f"Errore select-macchine: [{e}]")
            sys.exit(1)
    #
    def select_informazioni(self):
        try:
            self.cursor.execute("""select * from informazioni;""")
            self.info = self.cursor.fetchall()
            return self.info
        except Exception as e:
            print(f"Errore select-macchine: [{e}]")
            sys.exit(1)
    #
    def insert_macchine(self):
        cat_choice = ['TR','DR']
        tipo_choice = ['2400','2000','1800','1600','1400','1200','1000','800','600','400']
        plc_choice = ['siemens','allen-bradley']

        usati = set()

        for _ in range(250):
            pp_num = random.randint(20000, 30000)
            pp = "pp" + str(pp_num)

            if pp in usati:
                continue

            usati.add(pp)

            cat = random.choice(cat_choice)
            tipo = random.choice(tipo_choice)
            plc = random.choice(plc_choice)

            self.cursor.execute(
                "INSERT INTO macchinari(piano_produzione, categoria, tipo, tipo_plc) VALUES (?,?,?,?)",
                (pp, cat, tipo, plc)
            )

        self.connection.commit()
    #
    def insert_informazioni(self, macchine, alarms):
        for m in macchine:
            for a in alarms:
                self.cursor.execute("insert into informazioni(id_macchinario, id_allarme) values(?,?)",(m[0], a[0]))
            #
        #
        self.connection.commit()
    #
#
if __name__ == "__main__":
    #
    run = Run()
    #
    print("first select:")
    macchine = run.select_macchine()
    alarms = run.select_alarms()
    # info = run.select_informazioni()
    #
    ### run.insert_macchine() # FUNZIONA PER INSERT CASUALE MACCHINE
    #
    #print(macchine) list[tuple()]
    '''for r in macchine:
        print(f"ID: [{r[0]}] | PP: [{r[1]}]")
    '''
    #
    ### run.insert_informazioni(macchine, alarms) # FUNZIONA 
    print("GG") 
    run.connection.close()
#