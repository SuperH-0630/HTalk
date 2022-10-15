# HTalk
基于Python-Flask的沟通交流平台。

## 初始化数据库
### 使用migration
```shell
$ flask db upgrade e6b4151608e7
$ flask shell
$ >>> from app.db import create_all  
$ >>> create_all()
$ >>> quit()
```

### 不使用migration
```shell
$ flask shell
$ >>> from app.db import create_all  
$ >>> create_all()
$ >>> quit()
```
