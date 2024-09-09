<!-- markdownlint-disable -->

<a href="../src/database_observer.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `database_observer.py`
Provide the DatabaseObserver class to handle database relation and state. 

**Global Variables**
---------------
- **DATABASE_NAME**


---

## <kbd>class</kbd> `DatabaseObserver`
The Database relation observer. 



**Attributes:**
 
 - <b>`relation_name`</b>:  The name of the relation to observe. 
 - <b>`database`</b>:  The database relation interface. 

<a href="../src/database_observer.py#L24"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(charm: CharmBase, relation_name: str)
```

Initialize the oserver and register event handlers. 



**Args:**
 
 - <b>`charm`</b>:  The parent charm to attach the observer to. 
 - <b>`relation_name`</b>:  The name of the relation to observe. 


---

#### <kbd>property</kbd> model

Shortcut for more simple access the model. 



---

<a href="../src/database_observer.py#L45"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_db`

```python
get_db() → Optional[DatasourcePostgreSQL]
```

Return a postgresql datasource model. 



**Returns:**
 
 - <b>`DatasourcePostgreSQL`</b>:  The datasource model. 


