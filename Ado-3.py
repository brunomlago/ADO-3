"""
ADO-3: Colisões e Conservação do Momento Linear

Feito por Bruno Morano do Lago e Fabio Nascimento Moura
Turma: BCCCAS4NA
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Rectangle
from matplotlib.widgets import Button, RadioButtons, TextBox


def cinetica(m, v):
    return 0.5 * m * v**2


def colisao_elastica(m1, m2, v1, v2):
    soma = m1 + m2
    return (((m1-m2)*v1 + 2*m2*v2) / soma,
            ((m2-m1)*v2 + 2*m1*v1) / soma)


def colisao_inelastica(m1, m2, v1, v2):
    u = (m1*v1 + m2*v2) / (m1+m2)
    return u, u


def grandezas(m1, m2, v1, v2, u1, u2, dt_ms):
    pa = m1*v1 + m2*v2
    pd = m1*u1 + m2*u2
    ka = cinetica(m1, v1) + cinetica(m2, v2)
    kd = cinetica(m1, u1) + cinetica(m2, u2)
    j1, j2 = m1*(u1-v1), m2*(u2-v2)
    return pa, pd, ka, kd, kd-ka, j1, j2, abs(j1)/(dt_ms/1000.0)


class Simulador:
    CASOS = {
        "1: massas iguais": (1.0, 1.0, 4.0, 0.0),
        "2: leve x pesado": (1.0, 4.0, 5.0, 0.0),
        "3: pesado x leve": (4.0, 1.0, 5.0, 0.0),
    }
    CAMPOS = ("m1", "m2", "v1", "v2", "contato")

    def __init__(self):
        self.modo, self.pausado, self.alterando = "Elastica", False, False
        self.t, self.dt_anim = 0.0, 0.025
        self.valores = [1.0, 1.0, 4.0, 0.0, 10.0]

        self.fig = plt.figure(figsize=(15, 8.5), facecolor="#f4f6f8")
        self.fig.canvas.manager.set_window_title("ADO-3 - Colisoes e Momento Linear")
        self.fig.suptitle("Colisoes e Conservacao do Momento Linear", fontsize=16, weight="bold", y=.975)

        self.ax = self.fig.add_axes([.055, .52, .57, .39], facecolor="white")
        self.ax_p = self.fig.add_axes([.68, .65, .13, .24], facecolor="white")
        self.ax_k = self.fig.add_axes([.845, .65, .13, .24], facecolor="white")
        self.ax_info = self.fig.add_axes([.68, .40, .295, .18], facecolor="white")
        self.ax_info.set_xticks([]); self.ax_info.set_yticks([])
        self.ax_info.set_title("Resultados", loc="left", fontsize=11, weight="bold")
        self.painel = self.ax_info.text(.03, .88, "", transform=self.ax_info.transAxes,
                                        family="monospace", fontsize=8.7, va="top")

        self.ax.set_xlim(-8, 8); self.ax.set_ylim(-.6, 2.6)
        self.ax.axhline(0, color="#333333", lw=1)
        self.ax.set_yticks([]); self.ax.set_xlabel("posicao x (m)")
        self.ax.set_title("Colisao frontal unidimensional", fontsize=13)
        self.x1_0, self.x2_0 = -5.5, 2.0
        self.bloco1 = Rectangle((0, 0), 1, 1, color="#2b7bbb", ec="#222222")
        self.bloco2 = Rectangle((0, 0), 1, 1, color="#ed8127", ec="#222222")
        self.ax.add_patch(self.bloco1); self.ax.add_patch(self.bloco2)
        self.rot1 = self.ax.text(0, 0, "1", ha="center", va="center", color="white", weight="bold")
        self.rot2 = self.ax.text(0, 0, "2", ha="center", va="center", color="white", weight="bold")
        self.msg = self.ax.text(.5, .92, "", transform=self.ax.transAxes, ha="center",
                                color="crimson", weight="bold")

        self._criar_controles()
        self._recalcular()
        self.anim = FuncAnimation(self.fig, self._atualizar, interval=25,
                                  blit=True, cache_frame_data=False)

    def _criar_controles(self):
        # Coluna esquerda
        ax_modo = self.fig.add_axes([.055, .29, .17, .15], facecolor="white")
        ax_modo.set_title("Tipo de colisao", fontsize=10, weight="bold")
        self.radio_modo = RadioButtons(ax_modo, ("Elastica", "Inelastica"))
        self.radio_modo.on_clicked(self._modo_mudou)

        ax_casos = self.fig.add_axes([.055, .075, .17, .17], facecolor="white")
        ax_casos.set_title("Casos predefinidos", fontsize=10, weight="bold")
        self.radio_casos = RadioButtons(ax_casos, tuple(self.CASOS))
        self.radio_casos.on_clicked(self._caso_mudou)

        # Centro inferior
        self.fig.text(.275, .435, "Parametros numericos", fontsize=11, weight="bold")
        labels = ("m1 (kg)", "m2 (kg)", "v1 (m/s)", "v2 (m/s)", "contato (ms)")
        ys = (.375, .315, .255, .195, .135)
        self.caixas = []
        for label, y, valor in zip(labels, ys, self.valores):
            ax_box = self.fig.add_axes([.37, y, .15, .038], facecolor="white")
            box = TextBox(ax_box, label + "  ", initial=f"{valor:g}")
            box.on_submit(self._texto_enviado)
            self.caixas.append(box)

        ax_aplicar = self.fig.add_axes([.275, .065, .11, .045])
        ax_pause = self.fig.add_axes([.405, .065, .11, .045])
        ax_reset = self.fig.add_axes([.535, .065, .11, .045])
        self.bt_aplicar = Button(ax_aplicar, "Aplicar valores", color="#dceaf7", hovercolor="#c6ddf2")
        self.bt_pause = Button(ax_pause, "Pausar")
        self.bt_reset = Button(ax_reset, "Reiniciar")
        self.bt_aplicar.on_clicked(self._aplicar_textos)
        self.bt_pause.on_clicked(self._pausar)
        self.bt_reset.on_clicked(self._reiniciar)
        self.status = self.fig.text(.275, .025, "Digite os valores e clique em Aplicar valores.",
                                    fontsize=9, color="#44515c")

    @staticmethod
    def _dimensoes(m):
        return .75 + .25*np.sqrt(m), .55 + .18*np.sqrt(m)

    def _ler_textos(self):
        try:
            vals = [float(c.text.replace(",", ".")) for c in self.caixas]
            if vals[0] <= 0 or vals[1] <= 0:
                raise ValueError("As massas devem ser maiores que zero.")
            if vals[4] <= 0:
                raise ValueError("O tempo de contato deve ser maior que zero.")
            return vals
        except ValueError as erro:
            self.status.set_text(f"Valor invalido: {erro}")
            self.status.set_color("crimson")
            return None

    def _aplicar_textos(self, _=None):
        vals = self._ler_textos()
        if vals is None: return
        self.valores = vals
        self.status.set_text("Valores aplicados com sucesso.")
        self.status.set_color("#267326")
        self._reiniciar(None)

    def _texto_enviado(self, _):
        self._aplicar_textos()

    def _recalcular(self):
        self.m1, self.m2, self.v1, self.v2, self.dt_ms = self.valores
        self.w1, self.h1 = self._dimensoes(self.m1)
        self.w2, self.h2 = self._dimensoes(self.m2)
        self.half = (self.w1+self.w2)/2
        self.tem_colisao = self.v1 > self.v2
        self.tc = (((self.x2_0-self.x1_0)-self.half)/(self.v1-self.v2)
                   if self.tem_colisao else np.inf)
        funcao = colisao_elastica if self.modo == "Elastica" else colisao_inelastica
        self.u1, self.u2 = funcao(self.m1, self.m2, self.v1, self.v2)
        self.dados = grandezas(self.m1,self.m2,self.v1,self.v2,self.u1,self.u2,self.dt_ms)
        self._atualizar_resultados()

    def _atualizar_resultados(self):
        pa,pd,ka,kd,dk,j1,j2,fm = self.dados
        tipo = "ELASTICA" if self.modo == "Elastica" else "PERFEITAMENTE INELASTICA"
        self.msg.set_text("" if self.tem_colisao else "SEM COLISAO: exige v1 > v2")
        self.painel.set_text(
            f"{tipo}\n"
            f"v1={self.v1:7.3f} m/s   v2={self.v2:7.3f} m/s\n"
            f"u1={self.u1:7.3f} m/s   u2={self.u2:7.3f} m/s\n"
            f"p: {pa:9.4f} -> {pd:9.4f} kg.m/s\n"
            f"K: {ka:9.4f} -> {kd:9.4f} J   Delta K={dk:9.4f} J\n"
            f"J1={j1:9.4f} N.s   J2={j2:9.4f} N.s\n"
            f"F media={fm:9.3f} N   (Delta t={self.dt_ms:.1f} ms)")
        for ax, vals, titulo, unidade in ((self.ax_p,(pa,pd),"Momento total","kg.m/s"),
                                          (self.ax_k,(ka,kd),"Energia cinetica","J")):
            ax.clear()
            bars = ax.bar(["Antes","Depois"], vals, color=["#7f7f7f","#4c9e4a"], width=.65)
            ax.set_title(titulo, fontsize=10); ax.set_ylabel(unidade, fontsize=9)
            ax.axhline(0,color="black",lw=.7); ax.tick_params(labelsize=9)
            limite=max(abs(vals[0]),abs(vals[1]),1e-6)*1.28
            ax.set_ylim(min(0,-.1*limite),limite)
            for bar, val in zip(bars, vals):
                ax.text(bar.get_x()+bar.get_width()/2, val, f"{val:.2f}", ha="center",
                        va="bottom" if val >= 0 else "top", fontsize=8)

    def _posicoes(self):
        if not self.tem_colisao or self.t <= self.tc:
            return self.x1_0+self.v1*self.t, self.x2_0+self.v2*self.t
        x1c, x2c = self.x1_0+self.v1*self.tc, self.x2_0+self.v2*self.tc
        tau = self.t-self.tc
        return x1c+self.u1*tau, x2c+self.u2*tau

    def _atualizar(self, _):
        if not self.pausado: self.t += self.dt_anim
        x1,x2 = self._posicoes()
        if self.modo == "Inelastica" and self.tem_colisao and self.t > self.tc:
            encontro = self.x1_0+self.v1*self.tc+self.w1/2
            tau = self.t-self.tc
            face = encontro+self.u1*tau
            x1, x2 = face-self.w1/2, face+self.w2/2
        self.bloco1.set_bounds(x1-self.w1/2,0,self.w1,self.h1)
        self.bloco2.set_bounds(x2-self.w2/2,0,self.w2,self.h2)
        self.rot1.set_position((x1,self.h1/2)); self.rot2.set_position((x2,self.h2/2))
        if min(x1,x2)<-9 or max(x1,x2)>9: self.t=0.0
        return self.bloco1,self.bloco2,self.rot1,self.rot2,self.msg

    def _modo_mudou(self, label):
        self.modo=label; self._reiniciar(None)

    def _caso_mudou(self, label):
        if self.modo != "Elastica":
            self.status.set_text("Os casos predefinidos pertencem a opcao elastica.")
            self.status.set_color("#9a6500"); return
        vals=(*self.CASOS[label], self.valores[4])
        self.alterando=True
        for box,val in zip(self.caixas,vals): box.set_val(f"{val:g}")
        self.alterando=False
        self.valores=list(vals); self._reiniciar(None)

    def _pausar(self, _):
        self.pausado=not self.pausado
        self.bt_pause.label.set_text("Continuar" if self.pausado else "Pausar")

    def _reiniciar(self, _):
        self.t=0.0; self._recalcular(); self.fig.canvas.draw_idle()

    def executar(self):
        plt.show()


if __name__ == "__main__":
    Simulador().executar()
