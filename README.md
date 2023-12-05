# MES_Simulation
## code.py 
is the simulation of an MES System for an robotic assembly line with graphical user internface. 

## wscode.py is the simulation of MES system with extention of WebService interface for registring new order and also fetching updates about the status of a registered order. 
the webserivce extension is implemented by Flask. 

## wstest.py 
is a simple code to call the provided service internface by wscode.py and register a new order via this WS interface.

## checkStatus.py 
checks the status of a given order by ID  through provided WS interface by Webservice extention on wscode.py.
