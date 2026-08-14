import asyncio
import json
import requests
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# ========================================
# GPU 서버의 Ollama 주소
# ========================================

OLLAMA_URL = "http://localhost:11434/api/chat"

MODEL = "gemma3:12b"


def call_ollama(messages):

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": messages,
            "stream": False,
            "format": "json"
        }
    )

    response.raise_for_status()

    return response.json()["message"]["content"]



async def main():

    server_params = StdioServerParameters(
    command=sys.executable,
    args=["mcp_server.py"]
)

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            # --------------------------------
            # MCP Server가 제공하는 Tool 확인
            # --------------------------------

            tools = await session.list_tools()

            print("=== MCP Tools ===")

            for tool in tools.tools:
                print(tool.name)

            print()

            # --------------------------------
            # 사용자 질문
            # --------------------------------

            user_question = input("질문: ")

            # --------------------------------
            # Gemma에게 어떤 Tool이 필요한지 판단
            # --------------------------------

            prompt = f"""
너는 ERP Assistant이다.

사용 가능한 Tool:

get_product_stock(product_code)

기능:
상품코드를 이용하여 상품의
상품명, 재고수량, 가격을 조회한다.

사용자의 질문을 분석하라.

Tool이 필요하면 반드시 다음 JSON 형식으로만 응답하라.

{{
  "tool": "get_product_stock",
  "arguments": {{
    "product_code": "상품코드"
  }}
}}

Tool이 필요하지 않으면

{{
  "tool": null
}}

사용자 질문:

{user_question}
"""

            decision = call_ollama([
                {
                    "role": "user",
                    "content": prompt
                }
            ])

            print("\n=== Gemma 판단 ===")
            print(decision)

            try:
                command = json.loads(decision)

            except json.JSONDecodeError:

                print("Gemma가 올바른 JSON을 반환하지 않았습니다.")
                return

            # --------------------------------
            # MCP Tool 호출
            # --------------------------------

            if command["tool"] == "get_product_stock":

                arguments = command["arguments"]

                result = await session.call_tool(
                    "get_product_stock",
                    arguments=arguments
                )

                print("\n=== MCP 결과 ===")
                print(result)

                # MCP 결과를 텍스트로 변환
                tool_result = ""

                for item in result.content:

                    if hasattr(item, "text"):
                        tool_result += item.text

                # --------------------------------
                # Gemma에게 결과 전달
                # --------------------------------

                final_prompt = f"""
사용자의 질문:

{user_question}

ERP 조회 결과:

{tool_result}

위 ERP 데이터를 이용해서
사용자에게 간단하고 자연스럽게 한국어로 답변하라.
"""

                answer = call_ollama([
                    {
                        "role": "user",
                        "content": final_prompt
                    }
                ])

                print("\n=== 최종 답변 ===")
                print(answer)

            else:

                answer = call_ollama([
                    {
                        "role": "user",
                        "content": user_question
                    }
                ])

                print("\n=== 최종 답변 ===")
                print(answer)


if __name__ == "__main__":

    asyncio.run(main())