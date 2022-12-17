import datetime
import pandas as pd
import pygal as pg
import streamlit as st
from IPython.display import HTML, display, display_svg
from pygal.style import DarkStyle

st.set_page_config(
    page_title="受講生進捗ダッシュボード（12月）",
    page_icon="✅",
    layout="wide",
)

# read csv from a github repo
dataset_url = "https://raw.githubusercontent.com/Taichi-ando/student_dashboard/master/受講生管理シート（架空）.csv"
base_html = """
<!DOCTYPE html>
<html>
  <head>
  <script type="text/javascript" src="http://kozea.github.com/pygal.js/javascripts/svg.jquery.js"></script>
  <script type="text/javascript" src="https://kozea.github.io/pygal.js/2.0.x/pygal-tooltips.min.js""></script>
  </head>
  <body>
    <figure>
      {rendered_chart}
    </figure>
  </body>
</html>
"""


# read csv from a URL
@st.experimental_memo
def get_data() -> pd.DataFrame:
    return pd.read_csv(dataset_url)


df = get_data()

st.title("受講生進捗ダッシュボード（12月）")

# df = pd.read_csv("/Users/ando/project/obenkyo/受講生管理シート（架空） - シート1 (1).csv")
df = df.rename(columns={"進捗度(%)": "進捗度"})
df["修了"] = df["進捗度"] == 100
df_mean = df.groupby("コース", as_index=False).mean()

df["加入日"] = pd.to_datetime(df["加入日"])
df_date = (
    df.groupby([pd.Grouper(key="加入日", freq="2M"), "コース"])
    .count()
    .unstack(fill_value=0)
    .stack()
    .reset_index()
)

today = datetime.datetime.now()
df_last_m = df[df["加入日"] < today - datetime.timedelta(days=30)]

df_g = df.groupby("学校名", as_index=False).count()
univ_names = df_g["学校名"]
df_univ_per = df_g["氏名"] / len(df)


kpi1, kpi2 = st.columns(2)

kpi1.metric(
    label="受講生数",
    value=len(df),
    delta=len(df) - len(df_last_m),
)

kpi2.metric(
    label="コース修了者数",
    value=len(df[df["進捗度"] == 100]),
    delta=len(df[df["進捗度"] == 100]) - len(df_last_m[df_last_m["進捗度"] == 100]),
)

st.markdown("### 各コースの修了率")
gauge = pg.SolidGauge(
    half_pie=False,
    inner_radius=0.6,
    style=DarkStyle(
        value_font_size=40,
        value_colors=("white"),
        background="transparent",
        plot_background="transparent",
    ),
)
gauge.value_formatter = lambda x: "{:.1f}%".format(x)


_ = [
    gauge.add(k, [{"value": v, "max_vlaue": 100}])
    for k, v in zip(df_mean["コース"], df_mean["修了"] * 100)
]

st.write((HTML(base_html.format(rendered_chart=gauge.render(is_unicode=True)))))

fig_col1, fig_col2 = st.columns(2)

with fig_col1:
    st.markdown("### 各コースの平均進捗度")
    chart = pg.HorizontalBar(
        print_values=True,
        style=DarkStyle(
            value_font_size=50,
            background="transparent",
            plot_background="transparent",
            label_font_size=20,
            major_label_font_size=20,
            legend_font_size=25,
        ),
        margin=50,
    )
    # chart.title = "各コースの平均進捗度"
    chart.value_formatter = lambda x: "{:.2f}%".format(x)

    _ = [chart.add(k, v) for k, v in zip(df_mean["コース"], df_mean["進捗度"])]
    # display(HTML(base_html.format(rendered_chart=chart.render(is_unicode=True))))

    fig1 = HTML(base_html.format(rendered_chart=chart.render(is_unicode=True)))
    st.write(fig1)

with fig_col2:
    st.markdown("### 各コースの進捗度分布")
    bar_chart = pg.Bar(
        style=DarkStyle(
            background="transparent",
            plot_background="transparent",
            label_font_size=20,
            major_label_font_size=20,
            legend_font_size=25,
        ),
        margin=50,
    )
    for c in df_mean["コース"]:
        df_c = df.loc[df["コース"] == c, "進捗度"]
        bins = int((df_c.max() - df_c.min()) / 10)
        l = (
            pd.cut(df_c, [i * 10 for i in range(12)], right=False)
            .value_counts()
            .to_list()[::-1]
        )
        bar_chart.add(c, l)
    bar_chart.x_labels = [str(i * 10) for i in range(11)]

    fig2 = HTML(base_html.format(rendered_chart=bar_chart.render(is_unicode=True)))
    st.write(fig2)


fig_col3, fig_col4 = st.columns(2)

with fig_col3:
    st.markdown("### 学校構成")
    pie_chart = pg.Pie(
        style=DarkStyle(
            background="transparent",
            plot_background="transparent",
            label_font_size=20,
            major_label_font_size=20,
            legend_font_size=25,
        )
    )
    _ = [pie_chart.add(k, v) for k, v in zip(univ_names, df_univ_per)]
    fig3 = HTML(base_html.format(rendered_chart=pie_chart.render(is_unicode=True)))
    st.write(fig3)

with fig_col4:
    st.markdown("### コース割合")
    chart = pg.StackedLine(
        x_label_rotation=-40,
        style=DarkStyle(
            background="transparent",
            plot_background="transparent",
            label_font_size=20,
            major_label_font_size=20,
            legend_font_size=25,
        ),
        margin=50,
        fill=True,
        interpolate="hermite",
    )
    chart.x_labels = df_date["加入日"].dt.strftime("%Y-%m").unique()
    _ = [
        chart.add(c, df_date.loc[df_date["コース"] == c, "氏名"].cumsum().to_list())
        for c in df_mean["コース"]
    ]

    fig4 = HTML(base_html.format(rendered_chart=chart.render(is_unicode=True)))
    st.write(fig4)


st.markdown("### Detailed Data View")
st.dataframe(df)
