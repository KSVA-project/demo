# Runnable 체인의 조합, | 파이프 연산자를 써서 순차적으로 처리 ->  RunnableSequence
    # 1. Input으로는 전체 dict이 들어와, question 값만 꺼냄
    # 2. retriever: query 문자열을 받아서 chroma 벡터 DB에서 유사한 문서들을 검색 -> 결과는 List[Document] 객체
    # 3. RunnableLambda(lambda docs: "\n\n".join([doc.page_content for doc in docs]))
    #    retriever의 검색된 문서리스트 doc가 하나로 합쳐짐
    
    # 최종 전체 dict 입력 -> "question"만 추출 (query string) -> Chroma에서 관련 문서 검색
    # -> 문서 내용만 꺼내서 하나로 합침 -> PromptTemplate에 전달될 context가 됨
    chain = (
        {
            "context": RunnableLambda(lambda x: x["question"]) 
            | retriever 
            | RunnableLambda(lambda docs: "\n\n".join([doc.page_content for doc in docs])),
            "question": RunnablePassthrough(),
            "user_name": RunnablePassthrough(),
            "user_years": RunnablePassthrough(),
            "user_location": RunnablePassthrough(),
            "user_employees": RunnablePassthrough(),
            "user_sales": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

[전체 입력 딕셔너리]
{
  "question": "인천 지역 지원사업 알려줘",
  "user_name": "김성훈",
  "user_years": "2년",
  ...
}
         │
         ▼
 ┌──────────────────────────────┐
 │ context:                     │
 │ RunnableLambda(lambda x:     │
 │     x["question"])           │
 └──────────────────────────────┘
         │ "인천 지역 지원사업 알려줘"
         ▼
 ┌──────────────────────────────┐
 │ retriever                    │
 │ (질문 기반 유사 문서 검색)   │
 └──────────────────────────────┘
         │ [Document, Document, ...]
         ▼
 ┌────────────────────────────────────────────────┐
 │ RunnableLambda(lambda docs:                    │
 │     "\n\n".join([doc.page_content for doc in   │
 │     docs]))  ← 문서 내용 합치기                │
 └────────────────────────────────────────────────┘
         │
         ▼
[PromptTemplate에 {context}로 삽입됨]