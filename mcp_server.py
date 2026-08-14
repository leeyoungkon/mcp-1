from mcp.server.mcpserver import MCPServer

mcp = MCPServer("test-server")

# 가상 ERP 데이터
PRODUCTS = {
    "A100": {
        "name": "프린터 토너",
        "stock": 15,
        "price": 85000
    },
    "A200": {
        "name": "A4 복사용지",
        "stock": 120,
        "price": 25000
    },
    "A300": {
        "name": "마우스",
        "stock": 0,
        "price": 35000
    }
}


@mcp.tool()
def get_product_stock(product_code: str) -> dict:
    """상품코드로 상품명, 현재 재고량, 가격을 조회한다."""

    product = PRODUCTS.get(product_code)

    if product is None:
        return {
            "result": "NOT_FOUND",
            "product_code": product_code
        }

    return {
        "result": "OK",
        "product_code": product_code,
        "name": product["name"],
        "stock": product["stock"],
        "price": product["price"]
    }


if __name__ == "__main__":
    mcp.run()