Ninux_rate_meter
================

**Sistema di Monitoraggio dei Nodi della Rete Ninux tramite il protocollo SNMP**

Il progetto si compone di Moduli Indipendenti che fanno riferimento allo stesso
Data Base le cui queries di generazione sono indicate nel file "SQL_query.mysql"

 - **Modulo engine** : Script in python per cattura dati
 - **Modulo www** : Script PHP e file HTML per la realizzazione   del sito
  
Qui risiedono i file appartenti al modulo "engine" ovvero il motore di cattura e 
archiviazione dei dati.
Al momento il programma lavora su una configurazione di dati  IF-MIB basata sulle antenne 
Ubiquity.
 
 - Modulo per la generazione dei dati di traffico:

	I file di questo gruppo risiedono nella radice  e sono degli script 
	Python. ("nxrm.py")
	Il file è eseguibile e non necessita di altro che di essere configurato per
	l'accesso al DataBase. (variabile DatBaseHost='xxx.xxx.xxx.xx) Inoltre devono essere definiti  che utente
   	e password nelle rispettive variabili "user" "password".(default "ninux" "ninux")
	Viene creato un file "diario.log" i cui record riportano in forma testuale i dati rilevati.
	Creare il file mail_account come da example_mail_account
	
 - Progetto per la rappresentazione dei dati WEB based 
 
	I files di questo gruppo risiedono nel repository					    [https://github.com/SalvatoreM/www_nxrm.git](https://github.com/SalvatoreM/www_nxrm.git)
	sono degli script in PHP e codice HTML. In questa cartella sono anche presenti due pacchetti 
	per la generazione dei grafici e un altro per la statistica delle visite al sito.
 	Ambedue i pacchetti sono Open Source e liberamente scaricabili da
	[http://en.christosoft.de/ ](http://en.christosoft.de/) e
	[http://naku.dohcrew.com/libchart/pages/introduction/](http://naku.dohcrew.com/libchart/pages/introduction/).
	La serie dei file consente la piena gestione del sito.
	La sola configurazione richiesta per rendere operativo il sito  è quella di 
	aggiornare, nel file "libreria.php", l'indirizzo dello host su cui risiede MySQL server.
 	
	
	    
