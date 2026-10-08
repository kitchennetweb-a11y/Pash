import asyncio,json
from playwright.async_api import async_playwright
Q="JSON.stringify({mode:st.mode,type:game.type,aw:game.awaiting&&[game.awaiting.kind,game.awaiting.target],items:itemsGroup.children.map(g=>g.userData.item),b:document.getElementById('bfa').textContent,said:lastSaid})"
async def proj(pg,expr):
    return await pg.evaluate(f"""(()=>{{const o={expr};const v=new THREE.Vector3();new THREE.Box3().setFromObject(o).getCenter(v);v.project(camera);return [(v.x+1)/2*innerWidth,(1-v.y)/2*innerHeight]}})()""")
async def waitFree(pg):
    for _ in range(60):
        if await pg.evaluate("!!game.awaiting&&!game.busy"):return
        await pg.wait_for_timeout(250)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=["--use-gl=swiftshader","--enable-unsafe-swiftshader","--autoplay-policy=no-user-gesture-required"])
        pg=await b.new_page(viewport={"width":1024,"height":768});errs=[];pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto("file:///tmp/claude-0/local.html");await pg.wait_for_timeout(1500)
        await pg.click("#go");await pg.wait_for_timeout(1500)
        await pg.screenshot(path="room.png")
        # furniture taps
        for f in ['book','table','lamp']:
            x,y=await proj(pg,f"furnById('{f}')");await pg.mouse.click(x,y);await pg.wait_for_timeout(1800)
            print("tap",f,await pg.evaluate("[lastSaid,document.getElementById('bfa').textContent,lightsOn]"))
        await pg.screenshot(path="dark.png")
        x,y=await proj(pg,"furnById('lamp')");await pg.mouse.click(x,y);await pg.wait_for_timeout(1500)
        # fallback speech: where_ball has no clip -> plays w_ball
        print("fallback",await pg.evaluate("JSON.stringify(fallbackFor('where_ball'))"),await pg.evaluate("JSON.stringify(fallbackFor('say_car'))"),await pg.evaluate("JSON.stringify(fallbackFor('this_belly'))"))
        # find with body: force eye/mouth checks
        await pg.click("#bFind")
        for r in range(4):
            await waitFree(pg);kind,tgt=await pg.evaluate("[game.awaiting.kind,game.awaiting.target]");print(" find",kind,tgt)
            if kind=='item':
                x,y=await proj(pg,f"itemById('{tgt}')");await pg.mouse.click(x,y)
            else:
                part={'head':'head','hand':'arm','belly':'belly','feet':'feet','ear':'ear','eye':'face','mouth':'face'}[tgt]
                pt={'eye':'screen.localToWorld(new THREE.Vector3(0,.1,0))','mouth':'screen.localToWorld(new THREE.Vector3(0,-.2,0))'}.get(tgt,'new THREE.Vector3()')
                await pg.evaluate(f"poke('{part}',{pt})")
            await pg.wait_for_timeout(400);print("  ->",await pg.evaluate("[game.score,document.getElementById('bfa').textContent]"))
        await pg.wait_for_timeout(5000)
        # moves game
        await pg.click("#bMoves")
        seen=set()
        for i in range(30):
            await pg.wait_for_timeout(500);s=await pg.evaluate("JSON.stringify([lastSaid,pose.name,+robotScale.toFixed(2),game.type])");seen.add(s)
            if i==6:await pg.screenshot(path="moves.png")
        print("moves states:",sorted(set(json.loads(x)[0] for x in seen)),"poses",sorted(set(str(json.loads(x)[1]) for x in seen)))
        # rapid pokes -> gentle
        await pg.click("#bDance");await pg.wait_for_timeout(200);await pg.evaluate("setMode('idle')")
        for i in range(6):await pg.evaluate("poke('head',new THREE.Vector3())")
        print("rapid pokes ->",await pg.evaluate("lastSaid"))
        # stats + parent corner
        await pg.wait_for_timeout(5500)
        btn=await pg.query_selector("#parentBtn");bb=await btn.bounding_box()
        await pg.mouse.move(bb['x']+10,bb['y']+10);await pg.mouse.down();await pg.wait_for_timeout(2100);await pg.mouse.up()
        print("parent open:",await pg.evaluate("!document.getElementById('parent').hidden"),await pg.evaluate("document.getElementById('pcSum').innerText.replace(/\\n/g,' | ')"))
        print("rows:",await pg.evaluate("[...document.querySelectorAll('#pcRows tr')].slice(0,6).map(r=>r.innerText.replace(/\\t/g,' ')).join(' / ')"))
        await pg.screenshot(path="parent.png")
        print("errors:",errs)
        await b.close()
asyncio.run(main())
