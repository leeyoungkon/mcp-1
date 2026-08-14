import asyncio
import json
import requests
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "gemma3:12b"


def call_ollama(messages, json_mode=False):

    body = {
        "model": MODEL,
        "messages": messages,
        "stream": False
    }

    if json_mode:
        body["format"] = "json"

    response = requests.post(
        OLLAMA_URL,
        json=body
    )

    response.raise_for_status()

    return response.json()["message"]["content"]


async def main():

    # --------------------------------
    # MCP Server 실행 정보
    # --------------------------------

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server.py"]
    )

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            await session.initialize()

            # --------------------------------
            # MCP Tool 목록 확인
            # --------------------------------

            tools = await session.list_tools()

            print("=== MCP Tools ===")

            for tool in tools.tools:
                print("-", tool.name)

            print()

            # --------------------------------
            # 사용자 질문
            # --------------------------------

            user_question = input("질문: ")

            # --------------------------------
            # Gemma가 Tool 및 파라미터 판단
            # --------------------------------

            decision_prompt = f"""
너는 ERP Assistant이다.

사용 가능한 Tool은 다음과 같다.

Tool 이름:
get_product_stock

기능:
상품코드를 이용하여
상품명, 현재 재고수량, 가격을 조회한다.

입력 파라미터:
product_code: string

사용자의 질문을 분석해서
이 Tool을 사용해야 하는지 판단하라.

Tool이 필요하면 반드시 다음 JSON 형식으로만 응답하라.

{{
  "tool": "get_product_stock",
  "arguments": {{
    "product_code": "상품코드"
  }}
}}

Tool이 필요하지 않으면:

{{
  "tool": null
}}

사용자 질문:

{user_question}
"""

            decision = call_ollama(
                [
                    {
                        "role": "user",
                        "content": decision_prompt
                    }
                ],
                json_mode=True
            )

            print("\n=== Gemma 판단 ===")
            print(decision)

            try:
                command = json.loads(decision)

            except json.JSONDecodeError as e:

                print("JSON 변환 오류:", e)
                return

            # --------------------------------
            # Tool이 필요하지 않은 경우
            # --------------------------------

            if command.get("tool") is None:

                answer = call_ollama(
                    [
                        {
                            "role": "user",
                            "content": user_question
                        }
                    ]
                )

                print("\n=== 최종 답변 ===")
                print(answer)

                return

            # --------------------------------
            # MCP Tool 호출
            # --------------------------------

            tool_name = command["tool"]
            arguments = command["arguments"]

            print("\n=== MCP Tool 호출 ===")
            print("Tool:", tool_name)
            print("Arguments:", arguments)

            result = await session.call_tool(
                tool_name,
                arguments=arguments
            )

            # --------------------------------
            # MCP 결과를 문자열로 변환
            # --------------------------------

            tool_result = ""

            for item in result.content:

                if hasattr(item, "text"):
                    tool_result += item.text

            print("\n=== MCP 결과 ===")
            print(tool_result)

            # --------------------------------
            # Gemma가 최종 자연어 답변 생성
            # --------------------------------

            final_prompt = f"""
사용자의 질문:

{user_question}

ERP 시스템 조회 결과:

{tool_result}

위 ERP 조회 결과만 이용해서
사용자의 질문에 간단하고 자연스럽게 한국어로 답변하라.

조회되지 않은 정보는 임의로 만들지 마라.
"""

            answer = call_ollama(
                [
                    {
                        "role": "user",
                        "content": final_prompt
                    }
                ]
            )

            print("\n=== 최종 답변 ===")
            print(answer)


if __name__ == "__main__":

    asyncio.run(main())