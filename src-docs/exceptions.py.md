<!-- markdownlint-disable -->

<a href="../src/exceptions.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `exceptions.py`
Exceptions used by the irc-bridge charm. 



---

## <kbd>class</kbd> `RelationDataError`
Exception raised when we don't have the expected data in the relation or no relation. 

Attrs:  msg (str): Explanation of the error. 

<a href="../src/exceptions.py#L46"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(msg: str)
```

Initialize a new instance of the RelationDataError exception. 



**Args:**
 
 - <b>`msg`</b> (str):  Explanation of the error. 





---

## <kbd>class</kbd> `SnapError`
Exception raised when an action on the snap fails. 

Attrs:  msg (str): Explanation of the error. 

<a href="../src/exceptions.py#L14"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(msg: str)
```

Initialize a new instance of the SnapError exception. 



**Args:**
 
 - <b>`msg`</b> (str):  Explanation of the error. 





---

## <kbd>class</kbd> `SynapseConfigurationFileError`
Exception raised when we can't parse the synapse configuration file. 

Attrs:  msg (str): Explanation of the error. 

<a href="../src/exceptions.py#L62"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(msg: str)
```

Initialize a new instance of the SynapseConfigurationFileError exception. 



**Args:**
 
 - <b>`msg`</b> (str):  Explanation of the error. 





---

## <kbd>class</kbd> `SystemdError`
Exception raised when an action on the systemd service fails. 

Attrs:  msg (str): Explanation of the error. 

<a href="../src/exceptions.py#L30"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(msg: str)
```

Initialize a new instance of the SystemdError exception. 



**Args:**
 
 - <b>`msg`</b> (str):  Explanation of the error. 





