from mcp.server.mcpserver import MCPServer
import mysql.connector


mcp = MCPServer("erp-server")


# --------------------------------
# MySQL 연결
# --------------------------------

def get_db_connection():

    return mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="byby3845",
        database="erpdb"
    )


# --------------------------------
# MCP Tool
# --------------------------------

@mcp.tool()
def get_product_stock(product_code: str) -> dict:
    """
    상품코드를 이용하여
    상품명, 현재 재고수량, 가격을 조회한다.
    """

    conn = get_db_connection()

    cursor = conn.cursor(dictionary=True)

    sql = """
        SELECT
            product_code,
            product_name,
            stock,
            price
        FROM product_stock
        WHERE product_code = %s
    """

    cursor.execute(sql, (product_code,))

    product = cursor.fetchone()

    cursor.close()
    conn.close()

    if product is None:

        return {
            "result": "NOT_FOUND",
            "product_code": product_code
        }

    return {
        "result": "OK",
        "product_code": product["product_code"],
        "name": product["product_name"],
        "stock": product["stock"],
        "price": product["price"]
    }


if __name__ == "__main__":

    mcp.run()