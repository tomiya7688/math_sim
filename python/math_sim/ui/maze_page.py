from __future__ import annotations

import threading
import time
import tkinter as tk
from tkinter import ttk

from math_sim.application import (
    MazePageState,
    MazePlaybackController,
    MazePlaySessionController,
    MazeRaceController,
    MazeSimulationService,
)
from math_sim.ui import theme

GENERATOR_LABELS = {
    "Recursive Backtracker": "backtracker", "Randomized Prim": "prim",
    "Randomized Kruskal": "kruskal", "Binary Tree": "binary_tree",
    "Sidewinder": "sidewinder", "Growing Tree": "growing_tree",
    "Aldous-Broder": "aldous_broder", "Wilson": "wilson",
}
SOLVER_LABELS = {
    "A*": "astar", "BFS": "bfs", "Bidirectional BFS": "bidirectional_bfs",
    "DFS": "dfs", "Greedy Best-First": "greedy", "Left-hand Rule": "left_hand",
    "Right-hand Rule": "right_hand", "Dead-End Filling": "dead_end",
    "Random Mouse": "random_mouse",
}
RACE_COLORS = {
    "A*": "#4f8cff", "BFS": "#33c481", "Bidirectional BFS": "#20b7c9",
    "DFS": "#ff9f43", "Greedy Best-First": "#b980ff", "Left-hand Rule": "#ff6b9a",
    "Right-hand Rule": "#f6c85f", "Dead-End Filling": "#7f8c8d", "Random Mouse": "#e74c3c",
}
NORTH, EAST, SOUTH, WEST = 1, 2, 4, 8
PLAYBACK_SPEEDS = (0.25, 0.5, 1.0, 2.0, 4.0)


def _populate_maze_page(
    app: tk.Misc,
    page: tk.Frame,
    service: MazeSimulationService,
    state: MazePageState,
) -> None:
    controls = tk.Frame(page, bg=theme.PANEL, width=315, highlightthickness=1, highlightbackground=theme.BORDER)
    controls.pack(side="left", fill="y", padx=(0, 14)); controls.pack_propagate(False)
    inner = tk.Frame(controls, bg=theme.PANEL); inner.pack(fill="both", expand=True, padx=20, pady=20)
    tk.Label(inner, text="Maze Lab", bg=theme.PANEL, fg=theme.TEXT, font=(theme.FONT_FAMILY, 15, "bold")).pack(anchor="w")
    tk.Label(inner, text="Generate, replay construction, solve, race, and play.", bg=theme.PANEL, fg=theme.MUTED,
             wraplength=255, justify="left", font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(5, 16))

    width_var, height_var, seed_var = tk.StringVar(value="24"), tk.StringVar(value="18"), tk.StringVar(value="42")
    generator_var, solver_var = tk.StringVar(value="Recursive Backtracker"), tk.StringVar(value="A*")
    status_var = tk.StringVar(value="Ready")

    def entry(label: str, var: tk.StringVar) -> None:
        tk.Label(inner, text=label, bg=theme.PANEL, fg=theme.MUTED, font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(0, 5))
        tk.Entry(inner, textvariable=var, bg=theme.PANEL_ALT, fg=theme.TEXT, insertbackground=theme.TEXT,
                 relief="flat", bd=0, highlightthickness=1, highlightbackground=theme.BORDER,
                 highlightcolor=theme.ACCENT, font=(theme.FONT_FAMILY, 10)).pack(fill="x", ipady=7, pady=(0, 11))

    entry("Width", width_var); entry("Height", height_var); entry("Seed", seed_var)
    for label, var, values in (("Generator", generator_var, tuple(GENERATOR_LABELS)), ("Solver", solver_var, tuple(SOLVER_LABELS))):
        tk.Label(inner, text=label, bg=theme.PANEL, fg=theme.MUTED, font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(0, 5))
        ttk.Combobox(inner, textvariable=var, values=values, state="readonly").pack(fill="x", pady=(0, 11), ipady=4)

    def action(text: str, accent: bool = False) -> tk.Button:
        b = tk.Button(inner, text=text, relief="flat", bd=0, bg=theme.ACCENT if accent else theme.PANEL_ALT,
                      fg="white" if accent else theme.TEXT, activebackground=theme.ACCENT_HOVER if accent else theme.BORDER,
                      activeforeground=theme.TEXT, font=(theme.FONT_FAMILY, 10 if accent else 9, "bold"), cursor="hand2")
        b.pack(fill="x", ipady=9 if accent else 8, pady=(4 if accent else 0, 8)); return b

    generate_btn = action("GENERATE MAZE", True)
    generation_replay_btn = action("REPLAY GENERATION")
    compare_btn = action("COMPARE SOLVERS")
    race_btn = action("AI RACE")
    play_btn = action("PLAY")
    hint_btn = action("HINT: NEXT STEP")
    solution_var = tk.BooleanVar(value=False)
    tk.Checkbutton(inner, text="Show solver path", variable=solution_var, bg=theme.PANEL, fg=theme.MUTED,
                   selectcolor=theme.PANEL_ALT, activebackground=theme.PANEL, activeforeground=theme.TEXT,
                   font=(theme.FONT_FAMILY, 9)).pack(anchor="w", pady=(3, 8))
    tk.Label(inner, textvariable=status_var, bg=theme.PANEL, fg=theme.MUTED, wraplength=255,
             justify="left", font=(theme.FONT_FAMILY, 9)).pack(anchor="w")

    view = tk.Frame(page, bg=theme.PANEL, highlightthickness=1, highlightbackground=theme.BORDER)
    view.pack(side="left", fill="both", expand=True)
    header = tk.Frame(view, bg=theme.PANEL); header.pack(fill="x", padx=16, pady=(14, 8))
    tk.Label(header, text="Maze", bg=theme.PANEL, fg=theme.TEXT, font=(theme.FONT_FAMILY, 15, "bold")).pack(side="left")
    summary_var = tk.StringVar(value="No maze generated")
    tk.Label(header, textvariable=summary_var, bg=theme.PANEL, fg=theme.MUTED, font=(theme.FONT_FAMILY, 9)).pack(side="right")
    canvas = tk.Canvas(view, bg="#080a0d", highlightthickness=0, takefocus=True)
    canvas.pack(fill="both", expand=True, padx=14, pady=(0, 8))

    playback = tk.Frame(view, bg=theme.PANEL_ALT, highlightthickness=1, highlightbackground=theme.BORDER)
    playback.pack(fill="x", padx=14, pady=(0, 8))
    playback_status_var = tk.StringVar(value="Search 0 / 0 · 1x")
    tk.Label(playback, textvariable=playback_status_var, bg=theme.PANEL_ALT, fg=theme.MUTED,
             font=(theme.FONT_FAMILY, 9)).pack(side="left", padx=(10, 8))
    def small(text: str) -> tk.Button:
        b=tk.Button(playback,text=text,relief="flat",bd=0,bg=theme.PANEL,fg=theme.TEXT,activebackground=theme.BORDER,
                    activeforeground=theme.TEXT,font=(theme.FONT_FAMILY,9,"bold"),cursor="hand2",padx=8,pady=5)
        b.pack(side="left",padx=2,pady=5); return b
    reset_btn, play_replay_btn, pause_btn = small("⏮"), small("▶"), small("⏸")
    step_btn, slower_btn, faster_btn = small("⏭ 1"), small("− speed"), small("+ speed")

    metrics=tk.Frame(view,bg=theme.PANEL); metrics.pack(fill="x",padx=14,pady=(0,14))
    play_metrics_var=tk.StringVar(value="Moves — | Time — | Optimal — | Loss — | Efficiency —")
    compare_var=tk.StringVar(value="")
    playback_logic = MazePlaybackController(state)
    play_logic = MazePlaySessionController(state)
    race_logic = MazeRaceController()
    tk.Label(metrics,textvariable=play_metrics_var,bg=theme.PANEL_ALT,fg=theme.TEXT,anchor="w",padx=12,pady=8,
             font=(theme.FONT_FAMILY,9),highlightthickness=1,highlightbackground=theme.BORDER).pack(fill="x",pady=(0,6))
    tk.Label(metrics,textvariable=compare_var,bg=theme.PANEL_ALT,fg=theme.TEXT,anchor="w",justify="left",padx=12,pady=8,
             font=("Consolas",9),highlightthickness=1,highlightbackground=theme.BORDER).pack(fill="x")

    def params() -> dict:
        w,h,s=int(width_var.get()),int(height_var.get()),int(seed_var.get())
        if w<2 or h<2 or w>120 or h>90: raise ValueError("Width/height must be within 2..120 / 2..90")
        return {"width":w,"height":h,"seed":s,"generator":GENERATOR_LABELS[generator_var.get()],"solver":SOLVER_LABELS[solver_var.get()]}

    def center(x:int,y:int,cw:float,ch:float)->tuple[float,float]: return (x+.5)*cw,(y+.5)*ch
    def race_rows()->list[tuple[str,dict]]:
        rows=state.get("race_results"); return rows if isinstance(rows,list) else []
    def search_trace()->list:
        return playback_logic.search_trace()
    def generation_trace()->list:
        return playback_logic.generation_trace()
    def replay_total()->int:
        return playback_logic.total_frames()
    def update_replay_status()->None:
        mode={"search":"Search","generation":"Generation","race":"Race"}.get(str(state.get("mode")),"Replay")
        playback_status_var.set(f"{mode} {min(int(state.get('replay_frame',0)),replay_total())} / {replay_total()} · {float(state.get('replay_speed',1.0)):g}x")

    def dynamic_generation_walls(width:int,height:int,frame:int)->list[int]:
        return playback_logic.generation_walls(width, height, frame)

    def race_table(frame:int|None=None)->str:
        return race_logic.race_table(race_rows(), frame)

    def draw()->None:
        r=state.get("result")
        if not isinstance(r,dict):return
        width,height=int(r.get("width",0)),int(r.get("height",0)); final_walls=r.get("walls")
        if not isinstance(final_walls,list) or width<=0 or height<=0:return
        frame=int(state.get("replay_frame",0)); mode=state.get("mode")
        walls=dynamic_generation_walls(width,height,min(frame,len(generation_trace()))) if mode=="generation" else final_walls
        canvas.delete("all"); cw=max(canvas.winfo_width(),200)/width; ch=max(canvas.winfo_height(),200)/height
        if mode=="search":
            trace=search_trace()
            for p in trace[:min(frame,len(trace))]:
                if isinstance(p,(list,tuple)) and len(p)==2:
                    x,y=map(int,p); canvas.create_rectangle(x*cw+1,y*ch+1,(x+1)*cw-1,(y+1)*ch-1,fill=theme.PANEL_ALT,outline="")
            if frame>0 and trace:
                x,y=map(int,trace[min(frame,len(trace))-1]); canvas.create_rectangle(x*cw+2,y*ch+2,(x+1)*cw-2,(y+1)*ch-2,fill="#3a4b63",outline="")
        elif mode=="race":
            cells=set()
            for _,rr in race_rows():
                trace=rr.get("trace",[])
                for p in trace[:min(frame,len(trace))]:
                    if isinstance(p,(list,tuple)) and len(p)==2: cells.add((int(p[0]),int(p[1])))
            for x,y in cells: canvas.create_rectangle(x*cw+1,y*ch+1,(x+1)*cw-1,(y+1)*ch-1,fill=theme.PANEL_ALT,outline="")
            for label,rr in race_rows():
                trace=rr.get("trace",[])
                if frame>0 and trace:
                    x,y=map(int,trace[min(frame,len(trace))-1]); cx,cy=center(x,y,cw,ch); q=max(2.5,min(cw,ch)*.16)
                    canvas.create_oval(cx-q,cy-q,cx+q,cy+q,fill=RACE_COLORS[label],outline="#111111")
            compare_var.set(race_table(frame))
        elif mode=="generation" and frame>0:
            edge=generation_trace()[min(frame,len(generation_trace()))-1]
            if isinstance(edge,(list,tuple)) and len(edge)==4:
                ax,ay,bx,by=map(int,edge); cx,cy=center(bx,by,cw,ch); q=max(2.5,min(cw,ch)*.16)
                canvas.create_oval(cx-q,cy-q,cx+q,cy+q,fill=theme.ACCENT,outline="")

        if solution_var.get() and mode=="search":
            path=r.get("path",[])
            if isinstance(path,list) and len(path)>1:
                coords=[v for x,y in path for v in center(int(x),int(y),cw,ch)]; canvas.create_line(*coords,fill=theme.ACCENT,width=max(2,min(cw,ch)*.22))
        hint=state.get("hint")
        if isinstance(hint,tuple) and mode=="search":
            x,y=hint; canvas.create_rectangle(x*cw+2,y*ch+2,(x+1)*cw-2,(y+1)*ch-2,fill="#5a5130",outline="")
        for y in range(height):
            for x in range(width):
                wall=int(walls[y*width+x]); x0,y0,x1,y1=x*cw,y*ch,(x+1)*cw,(y+1)*ch; lw=max(1,min(cw,ch)*.10)
                if wall&NORTH:canvas.create_line(x0,y0,x1,y0,fill="#cfd6df",width=lw)
                if wall&EAST:canvas.create_line(x1,y0,x1,y1,fill="#cfd6df",width=lw)
                if wall&SOUTH:canvas.create_line(x0,y1,x1,y1,fill="#cfd6df",width=lw)
                if wall&WEST:canvas.create_line(x0,y0,x0,y1,fill="#cfd6df",width=lw)
        rr=max(3,min(cw,ch)*.24); sx,sy=center(0,0,cw,ch); gx,gy=center(width-1,height-1,cw,ch)
        canvas.create_oval(sx-rr,sy-rr,sx+rr,sy+rr,fill=theme.SUCCESS,outline=""); canvas.create_oval(gx-rr,gy-rr,gx+rr,gy+rr,fill=theme.ERROR,outline="")
        if mode=="search":
            px,py=state.get("player",(0,0)); pcx,pcy=center(int(px),int(py),cw,ch); pr=max(3,min(cw,ch)*.18)
            canvas.create_oval(pcx-pr,pcy-pr,pcx+pr,pcy+pr,fill="#fff",outline="#111")
        update_replay_status()

    def cancel_job()->None:
        job=state.get("replay_job")
        if job is not None:
            try:app.after_cancel(job)
            except Exception:pass
        state["replay_job"]=None
    def pause_replay()->None:
        playback_logic.pause()
        cancel_job()
        update_replay_status()
    def replay_tick()->None:
        state["replay_job"]=None
        if not state.get("replaying"):return
        if not playback_logic.advance():
            draw(); status_var.set("Replay finished."); return
        draw(); speed=max(float(state.get("replay_speed",1.0)),.01)
        state["replay_job"]=app.after(max(10,int(120/speed)),replay_tick)
    def start_replay()->None:
        if not playback_logic.start():
            status_var.set("No replay trace is available.");return
        replay_tick()
    def reset_replay()->None:
        pause_replay(); playback_logic.reset(); draw()
    def step_replay()->None:
        pause_replay(); playback_logic.step(); draw()
    def change_speed(d:int)->None:
        speed=playback_logic.change_speed(d)
        if state.get("replaying"):
            cancel_job(); state["replay_job"]=app.after(max(10,int(120/speed)),replay_tick)
        update_replay_status()

    def update_play_metrics()->None:
        r=state.get("result")
        if not isinstance(r,dict):return
        metrics=play_logic.metrics(
            int(r.get("optimal_steps",0)),
            time.perf_counter() if state.get("playing") else None,
        )
        play_metrics_var.set(
            f"Moves {metrics.moves} | Time {metrics.elapsed:.1f}s | "
            f"Optimal {metrics.optimal_steps} | Loss +{metrics.extra_steps} "
            f"({metrics.loss_percent:.1f}%) | Efficiency "
            f"{metrics.efficiency_percent:.1f}% | Backtracks {metrics.backtracks}"
        )
        if state.get("playing"):app.after(100,update_play_metrics)

    all_buttons=lambda:(generate_btn,generation_replay_btn,compare_btn,race_btn,play_btn)
    def finish(r:dict)->None:
        pause_replay(); state.update({"result":r,"race_results":[],"mode":"search","player":(0,0),"playing":False,"moves":0,"backtracks":0,"visited_cells":{(0,0)},"elapsed":0.0,"hint":None,"replay_frame":0})
        summary_var.set(f"{r.get('generator','')} · {r.get('solver','')} · steps {int(r.get('steps',0))} · loss +{int(r.get('extra_steps',0))} ({float(r.get('loss_percent',0)):.1f}%) · calculations {int(r.get('calculation_count',0))}")
        compare_var.set(""); status_var.set("Maze generated. Replay construction/search or press PLAY.")
        for b in all_buttons():b.configure(state="normal")
        update_play_metrics();draw();canvas.focus_set()
    def fail(msg:str)->None:
        status_var.set(f"Error: {msg}")
        for b in all_buttons():b.configure(state="normal")
    def worker(p:dict)->None:
        try:app.after(0,finish,service.generate(**p))
        except Exception as e:app.after(0,fail,str(e))
    def generate()->None:
        try:p=params()
        except Exception as e:status_var.set(str(e));return
        pause_replay();state["playing"]=False
        for b in all_buttons():b.configure(state="disabled")
        status_var.set("Generating maze with native C++ engine…");threading.Thread(target=worker,args=(p,),daemon=True).start()
    def start_generation_replay()->None:
        r=state.get("result")
        if not isinstance(r,dict):status_var.set("Generate a maze first.");return
        if not generation_trace():status_var.set("No generation trace is available.");return
        pause_replay();state.update({"mode":"generation","race_results":[],"playing":False,"replay_frame":0});compare_var.set("");status_var.set("Generation replay ready. Press ▶.");draw()

    def calculate_all(base:dict)->list[tuple[str,dict]]:
        rows=[]
        for label,solver in SOLVER_LABELS.items():p=dict(base);p["solver"]=solver;rows.append((label,commander.generate(**p)))
        return rows
    def compare_worker(base:dict)->None:
        try:
            rows=calculate_all(base)
            table=race_logic.comparison_table(rows)
            app.after(0,lambda:compare_var.set(table));app.after(0,lambda:status_var.set("Solver comparison completed"));app.after(0,lambda:[b.configure(state="normal") for b in all_buttons()])
        except Exception as e:app.after(0,fail,str(e))
    def compare()->None:
        try:p=params()
        except Exception as e:status_var.set(str(e));return
        pause_replay()
        for b in all_buttons():b.configure(state="disabled")
        status_var.set("Comparing solvers on the same maze…");threading.Thread(target=compare_worker,args=(p,),daemon=True).start()
    def finish_race(rows:list[tuple[str,dict]])->None:
        pause_replay()
        if not rows:fail("No race results were produced.");return
        base=rows[0][1];state.update({"result":base,"race_results":rows,"mode":"race","playing":False,"replay_frame":0});summary_var.set(f"AI Race · {base.get('generator','')} · {len(rows)} solvers · optimal {int(base.get('optimal_steps',0))} steps");compare_var.set(race_table(0));status_var.set("AI Race ready. Press ▶.")
        for b in all_buttons():b.configure(state="normal")
        draw()
    def race_worker(base:dict)->None:
        try:app.after(0,finish_race,calculate_all(base))
        except Exception as e:app.after(0,fail,str(e))
    def start_race()->None:
        try:p=params()
        except Exception as e:status_var.set(str(e));return
        pause_replay();state["playing"]=False
        for b in all_buttons():b.configure(state="disabled")
        status_var.set("Preparing AI Race…");threading.Thread(target=race_worker,args=(p,),daemon=True).start()

    def start_play()->None:
        if not isinstance(state.get("result"),dict):status_var.set("Generate a maze first.");return
        if state.get("mode")!="search":state["mode"]="search";state["replay_frame"]=0
        pause_replay();play_logic.start(time.perf_counter());status_var.set("Playing: use Arrow keys or WASD.");canvas.focus_set();update_play_metrics();draw()
    def move(dx:int,dy:int)->None:
        r=state.get("result")
        if not isinstance(r,dict):return
        moved=play_logic.move(r,dx,dy,time.perf_counter())
        if not moved.moved:return
        if moved.finished:
            metrics=play_logic.metrics(int(r.get("optimal_steps",0)))
            status_var.set(
                f"CLEAR! {metrics.moves} moves · loss +{metrics.extra_steps} "
                f"({metrics.loss_percent:.1f}%) · {metrics.elapsed:.2f}s"
            )
            update_play_metrics()
        draw()

    def key(event)->str|None:
        mp={"up":(0,-1),"w":(0,-1),"down":(0,1),"s":(0,1),"left":(-1,0),"a":(-1,0),"right":(1,0),"d":(1,0)};k=event.keysym.lower()
        if k in mp:move(*mp[k]);return "break"
        return None
    def hint()->None:
        r=state.get("result")
        if not isinstance(r,dict):status_var.set("Generate a maze first.");return
        next_cell=play_logic.next_hint(r.get("optimal_path",[]))
        if next_cell is None:
            status_var.set("No next hint is available from the current position.");return
        draw();app.after(1300,lambda:(state.__setitem__("hint",None),draw()))

    generate_btn.configure(command=generate);generation_replay_btn.configure(command=start_generation_replay);compare_btn.configure(command=compare);race_btn.configure(command=start_race);play_btn.configure(command=start_play);hint_btn.configure(command=hint)
    reset_btn.configure(command=reset_replay);play_replay_btn.configure(command=start_replay);pause_btn.configure(command=pause_replay);step_btn.configure(command=step_replay);slower_btn.configure(command=lambda:change_speed(-1));faster_btn.configure(command=lambda:change_speed(1))
    solution_var.trace_add("write",lambda *_:draw());canvas.bind("<KeyPress>",key);canvas.bind("<Button-1>",lambda _e:canvas.focus_set());canvas.bind("<Configure>",lambda _e:draw())



class MazePage(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        service: MazeSimulationService | None = None,
        state: MazePageState | None = None,
    ) -> None:
        super().__init__(parent, bg=theme.BG)
        self.service = service or MazeSimulationService()
        self.state = state or MazePageState()
        _populate_maze_page(self, self, self.service, self.state)


def build_maze_page(app: tk.Misc, parent: tk.Widget) -> tk.Frame:
    del app
    return MazePage(parent)


__all__ = ["MazePage", "build_maze_page"]
