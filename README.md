# HTalk
基于Python-Flask的沟通交流平台。

## 初始化数据库
### 使用migration
```shell
$ flask db upgrade 566a5752c06e
$ flask shell
$ >>> create_all()
$ >>> quit()
```

### 不使用migration
```shell
$ flask shell
$ >>> create_all()
$ >>> quit()
```
