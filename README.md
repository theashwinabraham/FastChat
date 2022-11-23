# FastChat
CS 251 (Software Systems Lab) Course Project by
- Ananth Krishna Kidambi
- Ashwin Abraham
- Govind Kumar

This project aims to build a network of clients interacting with each other with the help of some servers acting as mediators. This is much like how WhatsApp operates. The main focus is to
- Obtain high throughput with limited resources dedicated to the servers
- At the same time ensuring low latency of individual message deliveries and E2E encryption between clients

[Problem Statement](https://docs.google.com/document/d/e/2PACX-1vQglWg-qGoA92pyHpn2IGVjrDX_jIKsN5EjgqCBtUnMUWoYqrsWrumPuW7wjOiqTBgtPDtuxKaJcW9D/pub)

> **_NOTE:_**  This application has been written and tested using python 3.11. Hence, it may not be compatible with older versions.

<h4> Features </h4>

The FastChat application has the following features
- Client Authentication
- End to end encryption of messages
- Messaging to offline clients
- Multi-server support
- Load balancing between servers
- Group messaging
- A terminal user interface (built using textual)

<h4> Procedure to run the application </h4>
Start the postgresql server (on the local host and port "5432").

`sudo service postgresql start`

Create the following databases in the server-
- authdb
- msg_storage
- groupdb

To do this, 
- open psql using `sudo -u postgres psql`
- create the databases using `CREATE DATABASE <database_name>;`

After this, on different terminals, run the following commands (in the mentioned sequence)-
- `python3 auth_server.py`
- `python3 server.py <id> <port number>` run this any number of times to get multiple servers
- `python3 client.py` run this any number of times to get multiple clients

<h4> Dependencies </h4>

The following python libraries were used, all of which can be installed using `pip`  

- `psycopg2`
- `end2end`
- `cryptography`
- `rsa`
- `socket`
- `json`
- `textual`
- `threading`

<h3> Description of the implementation </h3> 

The networking part of the application is implemented using the `socket` library.

Whenever a `server` is started, it registers itself with the auth_server. 
After atleast one `server` is running, whenever a client joins, it connects to the auth_server, and a new thread is created in the auth_server for interaction with the client. The client connects using an `end2end.Communicator`, which is an rsa-encrypted connection. Then the client sends his username and password, which the auth_server then verifies (or registers if the client is new) and then it redirects the client to a messaging server (implemented in `server.py`).

The redirection is done using an otp mechanism, where the auth_server sends the client the relevent server's `host`, `port` and an `otp`. The auth_server also shares this `otp` with the messaging server, which verifies the client. This is done so that the client doesn't connect to the messaging servers without authentication.

The load balancing also happens at the redirection step, where the auth_server sends the client to the server with the least load.

<h4> Direct Messaging </h4>

Whenever a message is to be sent from, say _Bob_ to _Alice_, the following steps happen (along with the encryption part described in the next section)-

1. _Bob_ sends the message to the messaging server that he is connected to.
2. _Bob_'s server stores the message in _Alice_'s table present in the `msg_storage` database.
3. _Alice_'s server retrieves the message from _Alice_'s table and sends it to _Alice_.

<h4> Message encryption </h4>

The messages are encrypted using the **Fernet encryption scheme**. The Fernet keys are sent using the **RSA scheme**. The RSA keys are generated when the client first signs up, and the public keys are stored on the server, so as to allow messaging to offline clients.

Whenever two clients (say Alice and Bob) try to communicate for the first time, i.e. say Bob tries to start the conversation by sending the messate "_Hi, Alice_" the following steps happen-

1. _Bob_ retrieves _Alice_'s **RSA public key** from the server.
2. _Bob_ generates a new **Fernet key** and stores it.
3. He then encrypts the same **Fernet key** using _Alice_'s **RSA public key** and sends it to the server.
4. He also encrypts "_Hi, Alice_" using the **Fernet key** and sends it to the server.
5. The server sends these messages to _Alice_ whenever she connects to the server. 
6. _Alice_ decrypts the message containing the **Fernet key** using her **private RSA key** and stores it. This key will be used for all subsequent encryptpion between _Alice_ and _Bob_.
7. She then decrypts the second message using the **Fernet key** to get the message "_Hi, Alice_".

Whenever either of them has to send another message after this, they follow steps __4__ and __7__, using the **Fernet key** generated earlier.

The encryption used in groups is described in the next section.

<h4> Groups </h4>

Groups can be created by any client. The client who creates the group is also its admin.

Whenever a group is created, the server adds a table to the `groupdb` database, which contains the list of clients present in the group and also the role of each person in the group. ALso, the admin generates and stores a **group Fernet key**.

The messages in the group are encrypted using a common Fernet key.

When the admin adds another client to the group, the Fernet key of the group is shared with the new user by the admin. The **group Fernet key** is encrypted using the **direct messaging Fernet key**, which, if not present is generated and shared using steps 1-6 described in the previous section.

Whenever a message is sent on the group by any member of the group, the server forwards this message to all other members of the group using the same method as direct messages are sent.
