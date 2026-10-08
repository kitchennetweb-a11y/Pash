import asyncio
from playwright.async_api import async_playwright
Q="JSON.stringify({mode:st.mode,type:game.type,aw:game.awaiting&&[game.awaiting.kind,game.awaiting.target],busy:game.busy,items:itemsGroup.children.map(g=>g.userData.item),score:game.score,bubble:document.getElementById('bfa').textContent})"
async def clickItem(pg,id):
    pos=await pg.evaluate(f"""(()=>{{const g=itemById('{id}');const v=new THREE.Vector3(g.position.x,.3,g.position.z).project(camera);
      return [(v.x+1)/2*innerWidth,(1-v.y)/2*innerHeight]}})()""")
    await pg.mouse.click(*pos)
async def waitFree(pg):
    for _ in range(40):
        if await pg.evaluate("!!game.awaiting&&!game.busy"):return
        await pg.wait_for_timeout(250)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=["--use-gl=swiftshader","--enable-unsafe-swiftshader","--autoplay-policy=no-user-gesture-required",
          "--use-fake-ui-for-media-stream","--use-fake-device-for-media-stream","--use-file-for-fake-audio-capture=/tmp/claude-0/mic.wav"])
        ctx=await b.new_context(viewport={"width":1024,"height":768},permissions=["microphone"])
        pg=await ctx.new_page();pg.on("pageerror",lambda e:print("ERR",e))
        await pg.goto("file:///tmp/claude-0/local.html");await pg.wait_for_timeout(1500)
        await pg.click("#go");await pg.wait_for_timeout(1500)
        # --- FIND
        await pg.click("#bFind")
        for r in range(4):
            await waitFree(pg);s=await pg.evaluate(Q);print("find",s)
            kind,target=await pg.evaluate("game.awaiting&&game.awaiting.kind"),await pg.evaluate("game.awaiting&&game.awaiting.target")
            if kind=='item':
                wrong=await pg.evaluate("itemsGroup.children.map(g=>g.userData.item).find(x=>x!==game.awaiting.target)")
                if r==0:
                    await clickItem(pg,wrong);await pg.wait_for_timeout(200);print(" wrong->",await pg.evaluate("document.getElementById('bfa').textContent"))
                    await pg.screenshot(path="find.png");await waitFree(pg)
                await clickItem(pg,target)
            else:
                await pg.evaluate(f"poke({{hand:'arm',head:'head',belly:'belly',feet:'feet'}}['{target}'],new THREE.Vector3())")
            await pg.wait_for_timeout(300);print(" after",await pg.evaluate("[game.score,document.getElementById('bfa').textContent]"))
        await pg.wait_for_timeout(4000);print("find end",await pg.evaluate(Q))
        # --- FEED
        await pg.click("#bFeed");await waitFree(pg);print("feed",await pg.evaluate(Q))
        await pg.screenshot(path="feed.png")
        await clickItem(pg,await pg.evaluate("game.awaiting.target"));await pg.wait_for_timeout(3500);print("feed end",await pg.evaluate(Q))
        # --- SAY (mic file loops speech)
        await pg.click("#bSay")
        for i in range(14):
            await pg.wait_for_timeout(1000)
            print("say",await pg.evaluate("JSON.stringify({type:game.type,listening:game.listening,rec:talk.rec,playing:talk.playing,clips:talk.clips,items:itemsGroup.children.map(g=>g.userData.item),b:document.getElementById('bfa').textContent})"))
        await pg.screenshot(path="say.png")
        await pg.click("#bDance");await pg.wait_for_timeout(300);print("interrupt",await pg.evaluate(Q))
        await b.close()
asyncio.run(main())
