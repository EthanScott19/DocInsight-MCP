class QueryValidator:

    @staticmethod
    def is_safe(sql):
        forbidden = ["DROP", "DELETE", "ALTER", "TRUNCATE", "INSERT", "UPDATE"]

        sql_upper = sql.upper()

        for word in forbidden:
            if word in sql_upper:
                return False

        return True

    @staticmethod
    def is_select(sql):
        return sql.strip().upper().startswith("SELECT")
