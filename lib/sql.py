###### SQL HANDLING STUFF ######
import lib.pgsql as pgsql
import datetime
def selectQuery(table, **options):
    reqStart = datetime.datetime.now()
    print("*** Function selectQuery was called on '%s'" % reqStart)
    user_columns = options.get('columns')
    if user_columns:
        columns = ','.join('{column}'.format(column=column) for column in user_columns)
    else:
            columns = "*"
    like_str, equal_str, values = inputToQueryString(options.get('like'), options.get('equal'))
    where = joinClauses(like_str, equal_str, options.get('where','1=1'))
    limit = options.get('limit','100')
    order = options.get('order', 'oid desc')
    offset = options.get('offset','0')
    hits = options.get('hits', False)
    sum = options.get('sum',False)
    #query = "SELECT {columns} FROM {table} WHERE {where} ORDER BY {order} LIMIT {limit} OFFSET {offset}".format(columns=columns, table=table, where=where, limit=limit, order=order, offset=offset)
    query = "SELECT {columns} FROM {table} WHERE {where} LIMIT {limit} OFFSET {offset}".format(columns=columns, table=table, where=where, limit=limit, offset=offset)
    countQuery = "SELECT count(1) from (SELECT {columns} FROM {table} WHERE {where}) as count".format(columns=columns, table=table, where=where)
    print query
    connection = pgsql.PGSql()
    connection.connect()
    data = False
    if not hits:
        print("SQL SELECT START: %s" % datetime.datetime.now())
        data = connection.query(query, False)
        print("SQL SELECT END: %s" % datetime.datetime.now())
    if sum:
        print("SQL COUNT START: %s" % datetime.datetime.now())
        total = connection.query(countQuery,False)
        print("SQL COUNT END: %s" % datetime.datetime.now())
    connection.close()
    reqEnd = datetime.datetime.now()
    print('RESPONSE TIME: %s FOR DATA SQL QUERIES' % (str(reqEnd - reqStart)))
    if data and sum:
        return data,total
    elif data:
        return data
    elif hits:
        return total
    else:
        return False

def inputToQueryString(like, equal):
    if not like:
        like = {}
    if not equal:
        equal = {}
    like_items, equal_items = list(like.items()), list(equal.items())
    like_str = joinOperatorExpressions(extract(like_items), 'AND', "LIKE")
    equal_str = joinOperatorExpressions(extract(equal_items), "AND")
    values = list(extract(like_items, 1)) + list(extract(equal_items, 1))
    return like_str, equal_str, values

def joinClauses(*clauses):
        '''Joins numerous clauses with the AND operator
        Arguments:
            *clauses -list of clauses to join
        Usage:
            clause = joinClauses('`user` LIKE 'name%', '`id` = 5')
        returns joined clauses'''
        return ' AND '.join(filter(lambda item: bool(item), clauses))

def joinOperatorExpressions(exps, operator, second_operator="=", value="?"):
        '''Joins numerous expressions with two operators (see below)
        Arguments:
            exps - iterable list of expressions to join
            operator - operator to use in joining expressions (OR, AND, LIKE, etc)
            second_operator - operator to join each expression and value (defaults to =)
            value - what to be used as a value with the second_operator (defaults to ?)
        Usage:
            joined_expr = joinOperatorExpressions(["date", "now"], "OR") # `date` = ? OR `now` = ?
            joined_expr = joinOperatorExpressions(["date", "now"], "OR", "LIKE", "'%'") # `date` LIKE '%' OR `now` LIKE '%'
        returns joined expressions as one string'''
        func = lambda item: "{column} {operator} {exp}".format(column=escapeColumn(item), operator=second_operator,exp=value)
        return joinExpressions(exps, operator, func)

def extract(values, index=0):
        '''Extracts the index value from each value
        Arguments:
            values - list of lists to extract from
            index - index to select from each sublist (optional, defaults to 0)
        Usage:
            columns = extract([["a", 1], ["b", 2]]) # ["a", "b"]
            values  = extract([["a", 1], ["b", 2]], 1) # [1, 2]
        returns list of selected elements'''
        return map(lambda item: item[index], values)

def escapeColumn(value):
        '''Escapes a column name
        Arguments:
            value - column name to escape
        Usage:
            escaped_column = escapeColumn("time") # `time`
        returns escaped column name'''
        return "`{column}`".format(column=value)

def joinExpressions(exps, operator, func=lambda item: item):
        '''Joins numerous expressions with an operator
        Arguments:
            exps - iterable list of expressions to join
            operator - operator to use in joining expressions (OR, AND, LIKE, etc)
            func - optional function to call on each expression before joining
        Usage:
            joined_expr = joinExpressions(["date = NOW", "id = 1"], "OR") # date = NOW OR id = 1
            joined_expr = joinExpressions(["date = NOW", "id = 1"], "OR", escapeColumn) # `date` = NOW OR `id` = 1
        returns joined expressions as one string'''
        new_op = " {op} ".format(op=operator)
        return new_op.join(func(exp) for exp in exps)