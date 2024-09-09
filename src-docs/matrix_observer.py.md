<!-- markdownlint-disable -->

<a href="../src/matrix_observer.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `matrix_observer.py`
Provide the DatabaseObserver class to handle database relation and state. 



---

## <kbd>class</kbd> `MatrixObserver`
The Matrix relation observer. 

<a href="../src/matrix_observer.py#L22"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

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

<a href="../src/matrix_observer.py#L37"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `get_matrix`

```python
get_matrix() → Optional[MatrixAuthProviderData]
```

Return a Matrix authentication datasource model. 



**Returns:**
 
 - <b>`MatrixAuthProviderData`</b>:  The datasource model. 

---

<a href="../src/matrix_observer.py#L45"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>function</kbd> `set_irc_registration`

```python
set_irc_registration(content: str) → None
```

Set the IRC registration details. 



**Args:**
 
 - <b>`content`</b>:  The registration content. 


