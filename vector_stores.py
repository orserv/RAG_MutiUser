from langchain_chroma import Chroma
import config_data as config


class VectorStoreService(object):
    def __init__(self, embedding):
        """
        :param embedding: 嵌入模型的传入
        """
        self.embedding = embedding

        self.vector_store = Chroma(
            collection_name=config.collection_name,
            embedding_function=self.embedding,
            persist_directory=config.persist_directory,
        )

    def get_retriever(self):
        """返回向量检索器，方便加入chain"""
        return self.vector_store.as_retriever(search_kwargs={"k": config.similarity_threshold})


if __name__ == '__main__':
    # from langchain_community.embeddings import DashScopeEmbeddings
    from langchain_openai import OpenAIEmbeddings
    import dotenv
    import os
    dotenv.load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY_FREE0")
    OPENAI_API_BASE = os.getenv("OPENAI_BASE_URL0")

    # 1. 初始化 Embedding 模型
    embeddings = OpenAIEmbeddings(
        model=config.embedding_model_name,
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_API_BASE
    )
    # 2. 初始化向量存储服务 (传入 embedding 对象)
    vector_service = VectorStoreService(embeddings)
    # 3. 从服务中获取检索器 (Retriever)
    retriever = vector_service.get_retriever()
    res = retriever.invoke("我的体重180斤，尺码推荐")
    print(res)
