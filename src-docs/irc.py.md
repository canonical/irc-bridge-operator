<!-- markdownlint-disable -->

<a href="../src/irc.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `irc.py`
IRC Bridge charm business logic. 

**Global Variables**
---------------
- **IRC_BRIDGE_HEALTH_PORT**
- **IRC_BRIDGE_KEY_ALGO**
- **IRC_BRIDGE_KEY_OPTS**
- **IRC_BRIDGE_SNAP_NAME**
- **SNAP_PACKAGES**


---

## <kbd>class</kbd> `IRCBridgeService`
IRC Bridge service class. 

This class provides the necessary methods to manage the matrix-appservice-irc service. The service requires a connection to a (PostgreSQL) database and to a Matrix homeserver. Both of these will be part of the configuration file created by this class. Once the configuration file is created, a PEM file will be generated and an app registration file. The app registration file will be used to register the bridge with the Matrix homeserver. PEM and the configuration file will be used by the matrix-appservice-irc service. 




---

<a href="../src/irc.py#L131"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `configure`

```python
configure(
    db: DatasourcePostgreSQL,
    matrix: MatrixAuthProviderData,
    config: CharmConfig
) → None
```

Configure the service. 



**Args:**
 
 - <b>`db`</b>:  the database configuration 
 - <b>`matrix`</b>:  the matrix configuration 
 - <b>`config`</b>:  the charm configuration 

---

<a href="../src/irc.py#L202"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_registration`

```python
get_registration() → str
```

Return the app registration file content. 



**Returns:**
 
 - <b>`str`</b>:  the content of the app registration file 

---

<a href="../src/irc.py#L85"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `prepare`

```python
prepare() → None
```

Prepare the machine. 

Install the snap package and create the configuration directory and file. 

---

<a href="../src/irc.py#L66"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `reconcile`

```python
reconcile(
    db: DatasourcePostgreSQL,
    matrix: MatrixAuthProviderData,
    config: CharmConfig
) → None
```

Reconcile the service. 

Simple flow: 
- Check if the snap is installed 
- Check if the configuration files exist 
- Check if the service is running 



**Args:**
 
 - <b>`db`</b>:  the database configuration 
 - <b>`matrix`</b>:  the matrix configuration 
 - <b>`config`</b>:  the charm configuration 

---

<a href="../src/irc.py#L211"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `reload`

```python
reload() → None
```

Reload the matrix-appservice-irc service. 

Check if the service is running and reload it. 



**Raises:**
 
 - <b>`ReloadError`</b>:  when encountering a SnapError 

---

<a href="../src/irc.py#L226"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `start`

```python
start() → None
```

Start the matrix-appservice-irc service. 



**Raises:**
 
 - <b>`StartError`</b>:  when encountering a SnapError 

---

<a href="../src/irc.py#L239"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `stop`

```python
stop() → None
```

Stop the matrix-appservice-irc service. 



**Raises:**
 
 - <b>`StopError`</b>:  when encountering a SnapError 


---

## <kbd>class</kbd> `InstallError`
Exception raised when unable to install dependencies for the service. 





---

## <kbd>class</kbd> `ReloadError`
Exception raised when unable to reload the service. 





---

## <kbd>class</kbd> `StartError`
Exception raised when unable to start the service. 





---

## <kbd>class</kbd> `StopError`
Exception raised when unable to stop the service. 





