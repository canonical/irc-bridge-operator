<!-- markdownlint-disable -->

<a href="../src/matrix_observer.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `matrix_observer.py`
Provide the DatabaseObserver class to handle database relation and state. 



---

## <kbd>class</kbd> `MatrixObserver`
The Matrix relation observer. 

<a href="../src/matrix_observer.py#L17"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `__init__`

```python
__init__(charm: CharmBase, relation_name: str)
```

Initialize the oserver and register event handlers. 



**Args:**
 
 - <b>`charm`</b>:  The parent charm to attach the observer to. 
 - <b>`relation_name`</b>:  The name of the relation to observe 


---

#### <kbd>property</kbd> model

Shortcut for more simple access the model. 



---

<a href="../src/matrix_observer.py#L36"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `reconcile`

```python
reconcile() → Optional[DatasourceMatrix]
```

Reconcile the database relation. 



**Returns:**
 
 - <b>`Dict`</b>:  Information needed for setting environment variables. 


