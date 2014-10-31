#! /usr/bin/python
#============================================================================
#============================================================================
#============================================================================
#============================================================================
#============================================================================
#============================================================================
import MySQLdb as mdb
import os
import sys
import string
import time
import datetime
import random
import smtplib
from subprocess import Popen,PIPE
import base64
#============================================================================
#============================================================================
class logger():
	def __init__(self,logfile):
		self.reg=False
		self.report=False
		self.name=""
		self.path=""
		self.records=[]
		filename=string.split(logfile,"/")
		for f in filename[:-1]:
			self.path=self.path+f+"/"
		for f in filename[-1:]:
			self.name=self.name+f
#		print self.path+self.name
		if (not os.path.isfile(self.path+self.name)):
			dfile = open (self.path+self.name,"w")
			dfile.write ("Nuovo File del "+time.strftime("%c")+"\n")
			dfile.close
#============================================================================
#============================================================================
	def event_log(self,message):
#		print time.strftime("%H:%M")
#		print self.path+self.name
		dfile = open (self.path+self.name,"a")
#		print message
		dfile.write (message)
		dfile.close()
		self.archive()
#============================================================================
#============================================================================
	def archive(self):
		if (time.strftime("%H:%M") =="00:07"):
			if (not self.reg):
				os.system ("mv "+self.path+self.name+" "+self.path+time.strftime("%H:%M-%a-%b-%d-%Y")+self.name)
				self.reg=True
		elif (time.strftime("%H:%M") > "00:30"):
			if (self.reg):
				self.reg=False

#============================================================================
#============================================================================
	def send_report(self):
		if (time.strftime("%H:%M") =="03:00"):
			if (not self.report):
				f=open("/home/salvatore/engine_nxrm/mail_account","r")
				self.account=string.split(f.read(),"\n")
				f.close()
	#			print self.account
				self.user=string.split(self.account[1],",")[0]
				self.passw=string.split(self.account[1],",")[1]
				self.sender=string.split(self.account[2],",")[0]
				self.receiver=string.split(self.account[2],",")[1]
				self.provider=self.account[0]
				self.report=True
#                      "0123456789012345678901201234567890123450123456789001234567890112345656780123456789012012345678900"
#                                  22                   15           10        10          10           12        10        30
#				                      "--------------------------------------------------------------------------------------------------------------------"	
#			 	self.testo=self.testo+"|        Nodo          |    Indirizzo  | Rx Byte  | Tx Byte  | Attivita % |   Stato  |           Contatto           |"
#				                      "--------------------------------------------------------------------------------------------------------------------"
#                    	          "|RossiniMusicaDalleOnde|172.119.200.255|4294967296|4294967296|    100%    |Non Attivo|                              "
#				                      "--------------------------------------------------------------------------------------------------------------------"	
				self.testo="--------------------------------------------------------------------------------------------------------------------\n"	
			 	self.testo=self.testo+"|        Nodo          |    Indirizzo  | Rx Byte  | Tx Byte  | Attivita % |   Stato  |           Contatto           |\n"
				for rec in self.records:
					self.testo=self.testo+"|----------------------|---------------|----------|----------|------------|----------|------------------------------|\n"	
					self.testo=self.testo+rec
				self.testo=self.testo+"--------------------------------------------------------------------------------------------------------------------\n"	
				self.records=[]
				self.server=smtplib.SMTP(self.provider)
				self.server.login(self.user,base64.b64decode(self.passw))
				self.oggetto="NxRM  --  Report del giorno "+time.strftime("%A %d %B %Y")+" --"
				self.messaggio="From:%s\nTo:%s\nSubject:%s\n\n%s" %(self.sender,self.receiver,self.oggetto,self.testo)
				self.server.sendmail(self.sender,self.receiver,self.messaggio)
				self.server.quit()
				self.event_log ("["+time.strftime("%c")+"] "+"NxRM  --  Report del giorno "+time.strftime("%A %B %d %Y")+" --"+ " INVIATO a "+self.receiver+"\n")
		elif (time.strftime("%H:%M") > "03:30"):
			if (self.report):
				self.report=False
#============================================================================
#============================================================================
	def add_node_report(self,nodo,wip,in_b,out_b,act,stato,contatto):
		if (not len(contatto)):
			contatto="Non Conosciuto"
		else:
			contatto=contatto.split("@")[0]
		self.message="|"+nodo.center(22," ")+"|"+wip.center(15," ")+"|"+in_b.rjust(10," ")+"|"+out_b.rjust(10," ")+"|"+act.center(12," ")+"|"+stato.center(10," ")+"|"+contatto.center(30," ")+"|\n"
		self.event_log("["+time.strftime("%c")+"]:"+"Report : "+self.message)
		self.records.append(self.message)
		
#============================================================================
#============================================================================
#============================================================================
# Classe che relizza il comportamento di un Nodo.
# Sono definiti i metodi per campionare, attivare disattivare e rilevare i dati
# E' possibile riconoscere se un nodo e' attivo o no.
# Nel caso sia attivo questo viene campionato in media alla frequenza 
# configurata (12 campioni/ora)
# Nel caso non sia attivo  viene interrogato a frequenza dieci volte inferiore
#(1 Tentativo ogni ora)
# Quando un nodo non risponde alla richiesta di attivazione o di interrogazione
# viene messo in attesa e considerato non attivo.
#
#============================================================================
class NODO():
#============================================================================
# Inizializzazione Nodo:
# nodo_ref = Dizionario che descrive il nodo. Le chiavi sono i nomi delle colonne 
# della tabella nodi DB MysQL
# trate    = Periodo di campionamanto in secondi per nodo attivo
# twait    = Periodo di campionamneto se il nodo non risulta attivo
#============================================================================
	def __init__(self,nodo_ref,trate,twait,logobj):
		self.me = nodo_ref
		self.log=logobj
		self.first=True
#		logger.__init__(self,logfile)
		self.me["registrato"]=0
		self.last_status=False
		self.me["location"]=""
		self.registra()
		if (self.me["attivo"]):
			self.last_status=True
		self.twait=twait  # Periodo di campionamento se il nodo non e' attivo
		self.trate=trate	# Periodo di campionamento se il nodo e' attivo
		self.krand=3      # Variabile di scostamento random del periodo di campionamento
		self.tw=random.randint(self.twait-(self.twait/self.krand),self.twait+(self.twait/self.krand))
		self.tr=random.randint(0,self.trate)
		self.trm1=self.tr
		self.tic=0
		self.byte_in=0.0  # Byte al secondo in ingresso 
		self.byte_out=0.0 # Byte al secondo in uscita 
		self.last_time=time.time()  # Tempo assoluto dell'ultimo campionamento eseguito
		self.time_start=time.time()  # Tempo assoluto  di avvio per calcolo statistiche giornaliere (viene resettato ogni giorno)
		self.time_end=0 # Tempo assoluto  di fine (ore 00:00) per calcolo statistiche giornaliere (viene resettato ogni giorno)
		self.bin=0      
		self.bout=0
#  inizializzazione dati per statistica giornaliera
		self.acc_bin=0
		self.acc_bout=0
		self.acc_attivo=0
		self.acc_nonattivo=0			
		self.risposta=False
		self.init=True
		self.saved_today= False
		f=open("/home/salvatore/engine_nxrm/mail_account","r")
		self.account=string.split(f.read(),"\n")
		f.close()
#	print self.account
		self.user=string.split(self.account[1],",")[0]
		self.passw=string.split(self.account[1],",")[1]
		self.sender=string.split(self.account[2],",")[0]
		self.receiver=string.split(self.account[2],",")[1]
		self.provider=self.account[0]
#  Numero sequenziale di registrazione dati del nodo
		self.sequence = self.get_last_sequence()+1
		if (not self.sequence):
			self.sequence=0
#		print "sequence :",self.sequence,"\n"
#		log.event_log("Inzializzato  Nodo: "+self.me["nome"]+" Attivo ="+str(self.me["attivo"])+"\n")	
#============================================================================
#  Realizza la politica di interrogazione dei nodi
#  I Tempi di attesa per ogni nodo sono calcolati con una funzione random per
#  avere una distribuzione casuale uniforme in funzione del numero dei nodi:
#  SPERO !
#============================================================================
	def run(self):
		self.time_end=time.time()
		if ((time.time()-self.last_time) >= self.tr): # Tempo scaduto ?
#calcolo intervallo di tempo per il  prossimo campionamento
			self.trm1=self.tr
			self.tr=random.randint(self.trate-(self.trate/self.krand),self.trate+(self.trate/self.krand))
# rilevamento dati remoti 
			if (self.me ["attivo"]):
				if (not self.last_status):
					self.alert("Attivo")
				self.last_status=True
				if (not self.get_data()): # risposta ricevuta?
					if (not self.risposta): # non e' la prima volta che fallisce
						self.acc_nonattivo=self.acc_nonattivo+(self.time_end-self.last_time) 
						self.deactivate()  # dichiara disattivo il nodo
						self.sequence=self.sequence+2
					else:
						log.event_log ("["+time.strftime("%c")+"] "+"{"+str(int(self.acc_attivo))+"/"+str(int((self.time_end-self.time_start)))+" s}"+" Nodo :"+	self.me["nome"]+" " +self.me["ip_wifi"]+" Non Attivo"+" In="+str(int(self.bin))+" B/s"+" Out="+str(int(self.bout))+" B/s"+" next to "+str(self.tr)+"s in:"+"%3.2f"%(self.acc_bin/2**20)+" out:"+"%3.2f"%(self.acc_bout/2**20)+"\n")
						self.risposta=False; # il precedente test era fallito 
				else: #la risposta e' arrivata
#					self.acc_attivo=self.acc_attivo+(time.time()-self.last_time) 
					self.acc_attivo=self.acc_attivo+(self.time_end-self.last_time) 
					self.risposta=True 
					self.sequence=self.sequence+1
					log.event_log ("["+time.strftime("%c")+"] "+"{"+str(int(self.acc_attivo))+"/"+str(int((self.time_end-self.time_start)))+" s}"+" Nodo :"+self.me["nome"]+" "+self.me["ip_wifi"]+" Attivo"+" In="+str(int(self.bin))+" B/s"+" Out="+str(int(self.bout))+" B/s"+" next to "+str(self.tr)+"s in:"+"%3.2f"%(self.acc_bin/2**20)+" out:"+"%3.2f"%(self.acc_bout/2**20)+"\n")
				self.last_time=time.time() # aggiorna memoria temporale
			elif ((time.time()-self.last_time) >= self.tw): # Tempo scaduto per nodo disattivo ?
				self.acc_nonattivo=self.acc_nonattivo+(self.time_end-self.last_time) 
				self.tw=random.randint(self.twait-(self.twait/self.krand),self.twait+(self.twait/self.krand))
				log.event_log ("["+time.strftime("%c")+"] "+"Test Nodo: "+self.me["nome"]+" " +self.me["ip_wifi"]+" Non Attivo "+"next to "+str(self.tw)+"s"+"\n")
				if (self.last_status):
					self.alert("Non Attivo")
				self.last_status=False
				self.registra()	# tenta una nuova registrazione
				self.last_time=time.time() # aggiorna memoria temporale
			self.save_daily_data()
			log.send_report()

#============================================================================
# Attiva un nodo al campionamento dichiarandolo attivo 
# Provvede anche alla registrazione del contatto di Riferimento e 
# del luogo della antenna se  registrati nella configurazione del servizio
# SNMP sulla antenna;
# calcola l'indice del device wifi di comunicazione.
# (per le Ubiquity generalmente ath0) 
#============================================================================
	def registra (self):
		if(not self.me["registrato"]):
			self.me["contatto"]=self.get_contatto()
#			self.me["location"]=self.get_location()
			location=self.get_location()
			log.event_log ("Registra "+self.me["location"]+" "+self.me["contatto"]+"\n")
#			print "registra "+self.me["location"]," ",self.me["contatto"]
#		if (self.me["contatto"]<>"" and 	self.me["location"]<>""):
		if (self.me["contatto"]<>"" and 	location<>""):
			self.me["location"]=location
			index = self.get_index_if()
			if (index):
				log.event_log ("Registrato  Nodo :"+self.me["nome"]+" "+self.me["ip_wifi"]+"\n")
#				print "Registrato  Nodo :",self.me["nome"]," ",self.me["ip_wifi"]
				self.me["registrato"]=1
				self.me["attivo"] = 1
				self.update()
				self.risposta=True
			else:
				self.deactivate()
		else:
			self.deactivate()
#============================================================================
# Rileva il contatto  registrato del nodo  (es: miaposta@mailprovider.it)
#============================================================================
	def get_contatto(self):
#		result = os.popen("snmpget -c public -v1 "+self.me["ip_man"]+" SNMPv2-MIB::sysContact.0")
#---------------------------------------------------------------------------------------------------------
		cmd = "snmpget -c public -v1 "+self.me["ip_man"]+" SNMPv2-MIB::sysContact.0"
		p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
		r = p.stdout.read()
#---------------------------------------------------------------------------------------------------------
#		r=result.readline()
#		print "ho letto :  ",r,type(r)
		if (len(r)):
#			print string.split(r,": ")[1].strip("\n")
			return(string.split(r,": ")[1].strip("\n"))
		else:
			return ""
#============================================================================
# Rileva il luogo di posizionamento dell'antenna registrato del nodo  (es:Lippi)
#============================================================================
	def get_location(self):
#		result = os.popen("snmpget -c public -v1 "+self.me["ip_man"]+" SNMPv2-MIB::sysLocation.0")
#---------------------------------------------------------------------------------------------------------
		cmd = "snmpget -c public -v1 "+self.me["ip_man"]+" SNMPv2-MIB::sysLocation.0"
		p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
		r = p.stdout.read()
#		r = string.split(res,"\n")
#---------------------------------------------------------------------------------------------------------
#		r=result.readline()
		if (len(r)):
			return(string.split(r,": ")[1].strip("\n"))
		else:
			return ""
#============================================================================
# Ricerca l'indice di tabella della porta del nodo da monitorare
# (es: ath0 -> indice 5)
#============================================================================
	def get_index_if(self):
#		print "cerca "+self.me["interface"]
#		result = os.popen("snmpwalk -v 1 -c public "+self.me["ip_man"]+" interfaces.ifTable.ifEntry.ifDescr")
#---------------------------------------------------------------------------------------------------------
		cmd = "snmpwalk -v 1 -c public "+self.me["ip_man"]+" interfaces.ifTable.ifEntry.ifDescr"
		p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
		res = p.stdout.read()
		result = string.split(res,"\n")
#---------------------------------------------------------------------------------------------------------
		index = 0
#		for r in result.readlines():
		for r in result:
			if (len(r)):
				if ((string.find(r,self.me["interface"]) <> -1) and (string.find(r,self.me["interface"]+".") == -1)):
					self.me["index_if"]=str(index+1)
					return (index+1)
				index=index+1
			else:
				return(0)
		return (0)
#============================================================================
# Rileva i dati di campionamento se il nodo e' dichiarato attivo
# altrimenti provvede a verificare il ritono in attivita'
#============================================================================
	def  get_data(self):
#		result = os.popen("snmpget -t 2 -c public -v1 "+self.me["ip_man"]+" IF-MIB::ifOutOctets."+self.me["index_if"]+" IF-MIB::ifInOctets."+self.me["index_if"]+"  DISMAN-EVENT-MIB::sysUpTimeInstance")
#---------------------------------------------------------------------------------------------------------
		cmd = "snmpget -t 2 -c public -v1 "+self.me["ip_man"]+" IF-MIB::ifOutOctets."+self.me["index_if"]
		cmd=cmd+" IF-MIB::ifInOctets."+self.me["index_if"]+"  DISMAN-EVENT-MIB::sysUpTimeInstance"
		p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=True)
		res = p.stdout.read()
		r = string.split(res,"\n")
#---------------------------------------------------------------------------------------------------------
#		r=result.readlines()
#		print r
		if (len(r) >= 3):
			bo = string.split(r[0],": ")[1].strip("\n")
			bi = string.split(r[1],": ")[1].strip("\n")
			t = string.split(r[2]," (")[1]
			t=string.split(t,") ")[0].strip("\n")
#			if (self.init):
#				self.init=False
#				self.bout=float(bo)
#				self.bin=float(bi)
#			else:
			if (int(t)-self.tic):
				self.bout=(float(bo)-self.byte_out)*100/(int(t)-self.tic )
				self.bin=(float(bi)-self.byte_in)*100/(int(t)-self.tic )
			if (self.bout <0):
				self.bout=0
			if (self.bin <0):
				self.bin=0
			self.tic=int(t)
#--------------------------------------------------
# statistiche giornaliere
#--------------------------------------------------
			if(not self.first):
				self.delta_bin=float(bi)-self.byte_in
				if (self.delta_bin<0):	# condizione che si presenta a saturazione del contatore (4GB)
					if ((self.byte_in) < (2**31)): # il contatore era al disotto della meta' della sua capacita' (2GB)
						self.delta_bin=float(bi)	# si considera un possibile reset dei contatori
					else:
						self.delta_bin=2**32-self.byte_in+float(bi)
				self.acc_bin=self.acc_bin+self.delta_bin
#-------------------------------------------------------------------------------			
				self.delta_out=float(bo)-self.byte_out
				if (self.delta_out<0):	# condizione che si presenta a saturazione del contatore (4GB)
					if ((self.byte_out) < (2**31)):# il contatore era al disotto della meta' della sua capacita' (2GB)
						self.delta_out=float(bo) # si considera un possibile reset dei contatori
					else:
						self.delta_out=2**32-self.byte_out+float(bo)
				self.acc_bout=self.acc_bout+self.delta_out
#-------------------------------------------------------------------------------
#-------------------------------------------------------------------------------
			self.first=False
			self.byte_out=float(bo)
			self.byte_in=float(bi)
			self.save_data()
			return True
		else:
			return False
#===============================================================================
# Registra il nodo come  attivo, anche sul DB 
# Registra inoltre le credenziali di contatto e il luogo di istallazione
#===============================================================================
	def update (self):
		log.event_log ("["+time.strftime("%c")+"] "+"Riattivazione Nodo: "+self.me["nome"]+" " +self.me["ip_wifi"]+"\n")
#		print "Riattivazione Nodo: ",self.me["nome"]," " ,self.me["ip_wifi"]
		if (ninux_db.reopenDB("ninux_rate")):
			v={"registrato":'1',"attivo":'1',"contatto":self.me["contatto"],"location":self.me["location"],"index_if":self.me["index_if"]}
			ninux_db.update_record ("nodi",v,"ip_man ='"+self.me["ip_man"]+"'",debug =0 )
			self.me["registrato"]=1
			self.me["attivo"] = 1
			ninux_db.closeDB()
#============================================================================
# Registra il nodo come non attivo, anche sul DB per mancata risposta
#============================================================================
	def deactivate(self):
		log.event_log ("["+time.strftime("%c")+"] "+"Disattivazione Nodo: "+self.me["nome"]+" " +self.me["ip_wifi"]+"\n")
#		print "Disattivazione Nodo: ",self.me["nome"]," " ,self.me["ip_wifi"]
		if (ninux_db.reopenDB("ninux_rate")):
			ninux_db.update_record ("nodi",{"registrato":'0',"attivo":'0'} , "ip_man='"+self.me["ip_man"]+"'",debug =0 )
			self.me["registrato"]=0
			self.me["attivo"] = 0
			ninux_db.closeDB()
#============================================================================
# Salva i dati acquisiti nel DB MySQL : tabella "dati"
#============================================================================
	def save_data(self,debug=0):
#		t=string.split(time.strftime("%c")," ")
		t=string.split(time.strftime("%a %b %d %H:%M:%S %Y")," ")
#		print time.strftime("%a %b %d %H:%M:%S %Y")
#		print t[0],t[1],t[2],t[3],t[4]
		giorno=t[2]
		mese=t[1]
		anno=t[4]
		ora=t[3]
		valori={}
		valori["id_nodo"]=self.me["ID"]
		valori["interface"]=self.me["interface"]
		valori["byte_in"]=self.byte_in
		valori["byte_out"]=self.byte_out
		valori["tic_time"]=self.tic
		valori["byte_in_sec"]=self.bin
		valori["byte_out_sec"]=self.bout
		valori["in_byte_errors"]=0 #self.me[]
		valori["out_byte_errors"]=0 #self.me[]
		valori["cpu"]=0 #self.me[]
		valori["giorno"]= t[2]
		valori["mese"]=mese=t[1]
		valori["anno"]=t[4]
		valori["ora"]=t[3]
		valori["sequence"]=self.sequence
		valori["total_time"]=int(time.time())
		if (debug):
			print valori
		if (ninux_db.reopenDB("ninux_rate")):
			ninux_db.inserisci_record("dati",valori)
			ninux_db.closeDB()
#============================================================================
# Salva statistiche giornaliere  nel DB MySQL : tabella "report"
# i dati sono salvati dopo le ore 24 di ogni giorno
#============================================================================
	def save_daily_data(self,debug=0):
		if ((time.strftime("%H") == "23")  and  (not self.saved_today)):
			self.t=string.split(time.strftime("%a %b %d %H:%M:%S %Y")," ")
		if ((time.strftime("%H") == "00")  and  (not self.saved_today)):
			self.saved_today=True
#			self.time_end=time.time()
#			t=string.split(time.strftime("%a %b %d %H:%M:%S %Y")," ")
#			print time.strftime("%a %b %d %H:%M:%S %Y")
#			print t[0],t[1],t[2],t[3],t[4]
			giorno=self.t[2]
			mese=self.t[1]
			anno=self.t[4]
#			ora=t[3]
			valori={}
			valori["id_nodo"]=self.me["ID"]
			valori["byte_in"]=self.acc_bin
			valori["byte_out"]=self.acc_bout
#			valori["activity"]=int((self.acc_attivo/86400.0)*100)
			valori["activity"]=int((self.acc_attivo/(self.time_end-self.time_start))*100)
			valori["total_act"]=self.acc_attivo
			valori["total_noact"]=self.acc_nonattivo
			valori["status"]=self.me["attivo"]
			valori["giorno"]=giorno
			valori["mese"]=mese
			valori["anno"]=anno
#			valori["ora"]=t[3]
			if (debug):
				print valori
			if (ninux_db.reopenDB("ninux_rate")):
				ninux_db.inserisci_record("report",valori)
				ninux_db.closeDB()
			self.stato="NonAttivo"
			if (self.me["attivo"]):
				self.stato="Attivo" 
#			log.add_node_report(self.me["nome"],self.me["ip_wifi"],str(int(self.acc_bin)),str(int(self.acc_bout)),str(int((self.acc_attivo/86400.0)*100))+"%",self.stato,self.me["contatto"])
			log.add_node_report(self.me["nome"],self.me["ip_wifi"],"%3.2f"%(((self.acc_bin)/1048576.0)),"%3.2f"%(self.acc_bout/1045576.0),str(valori["activity"])+"%",self.stato,self.me["contatto"])
			self.acc_bin=0
			self.acc_bout=0
			self.acc_attivo=0	
			self.acc_noattivo=0
			self.time_start=time.time()
		elif (time.strftime("%H") > "00"):
			self.saved_today=False
				
#============================================================================
#============================================================================
# Invia una mail di alert per cambio di stato : 
#			da           "Attivo"     ====> "Non attivo"
# oppure 
#		 	da           "Non Attivo" ====> "Attivo" 
#============================================================================
	def alert (self,stato):
		if (self.me["mail"] == "hown"):
			self.server=smtplib.SMTP(self.provider)
			self.server.login(self.user,base64.b64decode(self.passw))
			self.oggetto="NxRM alert "+self.me['nome']+"@"+self.me['ip_wifi']
			self.testo="Il nodo %s@%s dalle ore %s del %s risulta %s" %(self.me['nome'],self.me['ip_wifi'],time.strftime("%H:%M"),time.strftime("%a-%d-%b-%Y"),stato)
			self.messaggio="From:%s\nTo:%s\nSubject:%s\n\n%s" %(self.sender,self.receiver,self.oggetto,self.testo)
			self.server.sendmail(self.sender,self.me["contatto"],self.messaggio)
			self.server.quit()
		log.event_log ("["+time.strftime("%c")+"] "+"Alert :"+self.me["nome"]+" " +self.me["ip_wifi"]+" il nodo risulta "+stato+"\n")
#		print "["+time.strftime("%c")+"] "+"Inviato Alert :"+self.me["nome"]+" " +self.me["ip_wifi"]+" il nodo risulta "+stato+"\n"
#============================================================================
# Ripristina l'ultimo valore di sequence: 
#============================================================================
#============================================================================
# Ripristina l'ultimo valore di sequence: 
#============================================================================
	def get_last_sequence(self):
		if (ninux_db.reopenDB("ninux_rate")):
			condizione='id_nodo='+str(self.me["ID"])+' and id=(select max(id) from dati where id_nodo='+str(self.me["ID"])+")"
			r=ninux_db.estrai_record("dati",["sequence","ID"],condizione)
			ninux_db.closeDB()
##			print r
			if (r):
				return (r[0]["sequence"])
			else:
				return False
		else:
			return False
#============================================================================
#============================================================================
#============================================================================
#============================================================================
#============================================================================
#============================================================================
#============================================================================
#============================================================================
# Classe Data Base che generalizza le principali operazioni
# di estrazione , inserimento e selezione dei dati
#============================================================================
class DB :
#============================================================================
# Inizializzazione per istanza
# Si definisce l'host su cui risiede il data base
# L'utente
# La password
#============================================================================
	def __init__ (self,host,user,passw,logobj, debug=0):
		self.host=host
		self.user=user
		self.passw=passw
		self.open=0
		self.log=logobj
		if (debug):
			print self.host,self.passw,self.user
#============================================================================
#============================================================================
#  Connessione allo Schema di riferimento
#  Rileva i nomi delle tablle dello schemo e i nomi delle colonne di
#  ogni tabella
#============================================================================
	def openDB (self,schema, debug=0):
		try:
			self.db= mdb.connect(host = self.host, user = self.user, passwd = self.passw, db = schema)
		except mdb.Error, e:
			self.log.event_log("Errore di Connessione DB")
#			print "Errore di Connessione DB"
			return (0)
		finally:
			self.tables=[]
			self.colonne={}
			self.open=1
			self.queryDB("show tables")
			self.tables=self.cur.fetchall()
			if (debug):
				print self.tables
			for t in self.tables:
				self.queryDB("show columns from "+t[0])
				cs=self.cur.fetchall()
				cc=[]
				for c in cs:
					cc.append(c[0])
				self.colonne[t[0]]=cc 	#dizionario key=tabella valore = [col1,col2...,coln]
				if (debug):
					print self.colonne 
			return (1)
#============================================================================
	def reopenDB (self,schema, debug=0):
		if (not self.open): 
			try:
				self.db= mdb.connect(host = self.host, user = self.user, passwd = self.passw, db = schema)
			except mdb.Error, e:
#				print "Errore di Connessione DB"
				self.log.event_log("Errore di Connessione DB")
				return (0)
			finally:
				self.open=1
				return (1)
		else:
			return (0)
#============================================================================
# Query generica
# Esegue anche la Commit
# Ritorna 0 se corretta
# Ritorna -1  se la sintassi non e' corretta o non c'e' connessione 
# (Protrebbe essere dichiarata Private) 
#============================================================================
	def queryDB (self,comand, debug=0):
		if (debug):
			print "query : "+ comand
		if (self.open):
			try:
				self.cur = self.db.cursor()
				self.cur.execute(comand)
			except mdb.Error, e:
				return (-1)
			finally:
				return (0)
		else:
				return (-1)
#============================================================================

#============================================================================
# Chiude la connessione con il Data VBase se aperta
# Ritorna 0 se corretto
# Ritorna -1 se non connesso
# ============================================================================
	def closeDB (self, debug=0):
		if (self.open):
			self.db.close()
			self.open=0
#============================================================================

#============================================================================
#  Esegue una commit della query attiva
#============================================================================
	def commitDB (self):
		if (self.open):
			try:
				self.db.commit()
			except mdb.Error, e:
				return (-1)
			finally:
				return (0)
		else:
				return (-1)
#============================================================================

#============================================================================
# Al momento non utilizata
#============================================================================
	def roolbackDB(self):
		self.db.rollback()
#============================================================================
	def get_colonne(self,tabella):
		return (self.colonne[tabella])
#============================================================================
# La funzione esegue una ricerca nei record di una tabella
#  tabella : Tabella di ricerca
#	colonne : colonne della tabella da estrarre (default tutte : *)
#	condizione : stringa delle condizioni (filtro)  di estrazione in stile SQL 
#			Esempio : "if_wifi='10.150.28.5' and if_man ='172.19.177.1'"
# Ritorna un array di dizionario le cui chiavi sono i nomi delle colonne della tabella
# Rtorna una lista vuota se non ci sono record che soddisfano le condizioni
# Ritorna  -1 se Data Base non connesso o la sintassi non e' corretta
#============================================================================
	def estrai_record(self,tabella,colonne=["*"],condizione='', debug=0):
		ret={}
		retval=[]
		query="select "
		if self.open :
			for c in colonne:
				query = query +c+", "
			query=query[:len(query)-2] 		#togliere l'ultima virgola
			query=query+" from "+tabella
			if (condizione !=''):
				query=query+ " where "+ condizione
			if (not self.queryDB(query)):
				results=self.cur.fetchall()
				if (len(colonne)==1):
					colonne = self.colonne[tabella]
				for row in results:
					i=0
					for r in row:
						ret[colonne[i]]=r
						i=i+1
					if (debug):
						print ret	
					retval.append(ret)
					ret={}
				if (debug):
					print retval
				return (retval) # Lista di Dizionari le cui chiavi sono i nomi delle colonne della tabella
			else:
				return (-1)
		else:
			return (-1)
#============================================================================
#============================================================================
# Inserisce un record nella tabella "tabella"
# i valori che sono in un dizionario:
# {'nome_colonna1': Valore,......,'nome_colonna1': Valore)
#  Ritorna 0 se il record e' inserito correttamente
#  Ritorna-1 se non inserito o la sintassi non e' corretta
#============================================================================
	def inserisci_record(self,tabella,valori,debug=0):
		if(self.open):
			query = "INSERT INTO "+tabella+ " ("
#        $query .= ' ('.$r.')';
			for v in valori.keys() :
				if (debug):
					print v
				query= query + v+ " ,"
			query=query[:len(query)-2] 		#togliere l'ultima virgola
			query =query +" ) VALUES ("
			for v in valori.values() :
				if (isinstance(v,str)):
					query=query +"'"+ v + "' ,"
				else:
					query=query +str(v)+ " ,"
			query=query[:len(query)-2] 		#togliere l'ultima virgola
			query =query + ")"
			if (debug):
				print query
			return (self.queryDB(query,debug))
#============================================================================

#============================================================================
# Aggiorna  i valori di un record esistenti
# della Tabella "tabella"
#  i valori da sostituire sono dischirati in dizionario
# {'nome_colonna1': Valore,......,nome_colonna1': Valore}
#
#  Ritorna 0 se il record e' inserito correttamente
#  Ritorna -1 se non aggiornato o la sintassi non e' corretta
#============================================================================
	def update_record (self,tabella,valori,condizione = "",debug = 0 ):
		if(self.open):
			query = "UPDATE "+tabella+" SET "
			for v in valori.keys():
				if (isinstance(valori[v],str)):
					query=query + v +" = '"+ valori[v]+"', "
				else:
					query=query + v +" = "+ valori[v]+", "
			query=query[:len(query)-2] 		#togliere l'ultima virgola
			if (len(condizione)):
				query=query + " WHERE "+ condizione
			if (debug):
				print query
			return (self.queryDB(query),debug)
	
#============================================================================
# Program Main 
#============================================================================
pathnome_log="/home/salvatore/engine_nxrm/diario.log"
log=logger(pathnome_log)
DataBaseHost='172.16.1.9'
user='ninux'
password='ninux'
ninux_db = DB (DataBaseHost,user,password,log) ## Istanzia il Data Base
ninux_db.openDB("ninux_rate")                ## Apre la connessione al Data Base
tutti_nodi = ninux_db.estrai_record("nodi") # Estrae tutti i nodi
ninux_db.closeDB()
i=0
log.event_log ( "---------------------------------------------------------"+"\n")
log.event_log ( "---------------------------------------------------------"+"\n")
for s in tutti_nodi:
	tutti_nodi[i] = NODO(s,300,1200,log)
	log.event_log ("%s %s %s %s %s %s %d\n" %(s["nome"],s["contatto"],s["ip_wifi"]," - ",s["ip_man"],"attivo = ",s["attivo"]))
	log.event_log ( "---------------------------------------------------------"+"\n")
	time.sleep(1)
	i=i+1
log.send_report()
while 1:
	for s in tutti_nodi:
		s.run()
#	print "-----------------------------------------------------------------"
	time.sleep(2)
	
