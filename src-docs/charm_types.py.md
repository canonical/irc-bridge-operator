<!-- markdownlint-disable -->

<a href="../src/charm_types.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

# <kbd>module</kbd> `charm_types.py`
Type definitions for the Synapse charm. 



---

## <kbd>class</kbd> `CharmConfig`
A named tuple representing an IRC configuration. 



**Attributes:**
 
 - <b>`ident_enabled`</b>:  Whether IRC ident is enabled. 
 - <b>`bot_nickname`</b>:  Bot nickname. 
 - <b>`bridge_admins`</b>:  Bridge admins. 


---

#### <kbd>property</kbd> model_extra

Get extra fields set during validation. 



**Returns:**
  A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`. 

---

#### <kbd>property</kbd> model_fields_set

Returns the set of fields that have been explicitly set on this model instance. 



**Returns:**
  A set of strings representing the fields that have been set,  i.e. that were not filled from defaults. 



---

<a href="../src/charm_types.py#L81"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>classmethod</kbd> `userids_to_list`

```python
userids_to_list(value: str) → List[str]
```

Convert a comma separated list of users to list. 



**Args:**
 
 - <b>`value`</b>:  the input value. 



**Returns:**
 The string converted to list. 



**Raises:**
 
 - <b>`ValidationError`</b>:  if user_id is not as expected. 


---

## <kbd>class</kbd> `DatasourcePostgreSQL`
A named tuple representing a Datasource PostgreSQL. 



**Attributes:**
 
 - <b>`user`</b>:  User. 
 - <b>`password`</b>:  Password. 
 - <b>`host`</b>:  Host (IP or DNS without port or protocol). 
 - <b>`port`</b>:  Port. 
 - <b>`db`</b>:  Database name. 
 - <b>`uri`</b>:  Database connection URI. 


---

#### <kbd>property</kbd> model_extra

Get extra fields set during validation. 



**Returns:**
  A dictionary of extra fields, or `None` if `config.extra` is not set to `"allow"`. 

---

#### <kbd>property</kbd> model_fields_set

Returns the set of fields that have been explicitly set on this model instance. 



**Returns:**
  A set of strings representing the fields that have been set,  i.e. that were not filled from defaults. 



---

<a href="../src/charm_types.py#L34"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square"></a>

### <kbd>classmethod</kbd> `from_relation`

```python
from_relation(model: Model, relation: Relation) → DatasourcePostgreSQL
```

Create a DatasourcePostgreSQL from a relation. 



**Args:**
 
 - <b>`relation`</b>:  The relation to get the data from. 
 - <b>`model`</b>:  The model to get the secret from. 



**Returns:**
 A DatasourcePostgreSQL instance. 


