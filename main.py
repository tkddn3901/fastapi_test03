# main.py




from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from database import get_db


# fastapi 객체 생성
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# jinja2 템플릿 객체 생성 (templates 파일들이 어디에 있는지 알려야 한다.)
templates = Jinja2Templates(directory="templates")



@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        # 응답에 필요한 data 를 context 로 전달 할수 있다.
        context={
            "fortuneToday":"동쪽으로 가면 귀인을 만나요"
        }
    )


# get 방식 /post 요청 처리
@app.get("/post", response_class=HTMLResponse)
def getPosts(request: Request, db:Session = Depends(get_db)):
    # DB 에서 글목록을 가져오기 위한 sql 문 준비
    query = text("""
        SELECT num, writer, title, content, created_at
        FROM post
        ORDER BY num DESC
    """)
    # 글 목록을 얻어와서
    result = db.execute(query)
    posts = result.fetchall()
    # 응답하기
    return templates.TemplateResponse(
        request=request,
        name="post/list.html", # templates/post/list.html jinja2 를 해석한 결과를 응답
        context={
            "posts":posts
        }
    )


@app.get("/post/new", response_class=HTMLResponse)
def postNewForm(request: Request):
    return templates.TemplateResponse(request=request, name="post/new-form.html")


@app.post("/post/new")
def postNew(writer: str = Form(...), title: str = Form(...), content: str = Form(...),
            db: Session = Depends(get_db)):
    # DB 에 저장할 sql 문  준비
    query = text("""
        INSERT INTO post
        (writer, title, content)
        VALUES(:writer, :title, :content)
    """)
    db.execute(query, {"writer":writer, "title":title, "content":content})
    db.commit()


    # 특정 경로로 요청을 다시 하도록 리다일렉트 응답을 준다.
    return RedirectResponse("/post", status_code=302)


@app.post("/post/delete")
def postDelete(num: int = Form(...),
            db: Session = Depends(get_db)):
    # DB 에 저장할 sql 문  준비
    query = text("""
        DELETE FROM post
        WHERE num=:num
    """)
    db.execute(query, {"num":num})
    db.commit()


    # 특정 경로로 요청을 다시 하도록 리다일렉트 응답을 준다.
    return RedirectResponse("/post", status_code=302)

@app.get("/post/update", response_class=HTMLResponse)
def postUpdateForm(request: Request, num: int, db: Session = Depends(get_db)):
    # 1. 전달받은 num을 이용해 해당 게시글 정보를 조회합니다.
    query = text("SELECT num, title, content FROM post WHERE num = :num")
    result = db.execute(query, {"num": num}).fetchone()
    
    # 2. 만약 해당 번호의 글이 없다면 (선택사항: 에러 처리나 리다이렉트)
    if result is None:
        return RedirectResponse("/post", status_code=303)

    # 3. 조회된 결과(result)를 'post'라는 이름으로 템플릿에 넘겨줍니다.
    return templates.TemplateResponse(
        request=request, 
        name="post/new-update.html", 
        context={"post": result}
    )


@app.post("/post/update")
def postUpdate(
    num: int = Form(...),      # HTML의 <input type="hidden" name="num"> 값을 받음
    title: str = Form(...), 
    content: str = Form(...),
    db: Session = Depends(get_db)
):
    # 1. 특정 번호(num)를 가진 행만 업데이트하도록 WHERE 절 추가
    query = text("""
        UPDATE post
        SET title = :title, content = :content
        WHERE num = :num
    """)
    
    # 2. 실행 시 num 값도 함께 전달
    db.execute(query, {"title": title, "content": content, "num": num})
    db.commit()

    return RedirectResponse("/post", status_code=302)