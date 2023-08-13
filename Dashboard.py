# -*- coding: utf-8 -*-
# # Skilldzire Project
# ## Importing Libraries

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as pl
import streamlit as st
from datetime import datetime
import copy

# ## Useful Functions

def color(val):
    try:
        if val < 0:
            return 'color:red;'
        elif val > 0:
            return 'color:green;'
        else :
            return None
    except:
        pass

# ## Loading and Cleaning Data

@st.cache_data
def load_data():
    # Loading CSV Files
    
    met_vid = pd.read_csv('Dataset/Aggregated_Metrics_By_Video.csv').iloc[1:,:]
    met_con_sub = pd.read_csv('Dataset/Aggregated_Metrics_By_Country_And_Subscriber_Status.csv')
    com_all = pd.read_csv('Dataset/All_Comments_Final.csv')
    vid_per = pd.read_csv('Dataset/Video_Performance_Over_Time.csv')
    
    # Cleaning CSV Files
    
    # Cleaning met_vid
    new_columns = ['Video', 'Video Title', 'Video Publish Time', 'Comments Added', 'Shares', 'Dislikes', 'Likes', 'Subscribers Lost', 'Subscribers Gained', 'RPM(USD)', 'CPM(USD)', 'Average Percentage Viewed(%)', 'Average View Duration', 'Views', 'Watch Time(Hours)', 'Subscribers', 'Your Estimated Revenue(USD)', 'Impressions', 'Impressions Click-through Rate(%)']
    
    met_vid.columns = new_columns
    met_vid[new_columns[2]] = pd.to_datetime(met_vid[new_columns[2]], format = 'mixed')
    met_vid[new_columns[12]] = met_vid[new_columns[12]].apply(lambda x: datetime.strptime(x,'%H:%M:%S')).dt.time
    met_vid['Average View Duration(sec)'] = met_vid['Average View Duration'].apply(lambda x: x.second + x.minute * 60 + x.hour * 3600)
    met_vid.sort_values(new_columns[2], inplace = True)

    # Cleaning vid_per
    vid_per['Date'] = pd.to_datetime(vid_per['Date'], format = 'mixed')

    # Cleaning com_all
    com_all['Date'] = pd.to_datetime(com_all['Date'], format = '%Y-%m-%dT%H:%M:%SZ')

    return met_vid, met_con_sub, com_all, vid_per


# ## Data Forming

met_vid, met_con_sub, com_all, vid_per = load_data()

temp_vid = copy.deepcopy(met_vid)

numeric_cols = np.array((temp_vid.dtypes == 'float64') | (temp_vid.dtypes == 'int64'))
median_vid = temp_vid[temp_vid.columns[numeric_cols]].median()

temp_vid.iloc[:,numeric_cols] = (temp_vid.iloc[:,numeric_cols] - median_vid).div(median_vid)
temp_vid['Video Publish Time'] = temp_vid['Video Publish Time'].apply(lambda x: x.date())

temp_vid_per = pd.merge(vid_per, met_vid.loc[:,['Video', 'Video Publish Time']], left_on = 'External Video ID', right_on = 'Video')
temp_vid_per['Days Published'] = (temp_vid_per['Date'] - temp_vid_per['Video Publish Time']).dt.days

views_by_days = pd.pivot_table(temp_vid_per, index = "Days Published", values = "Views", aggfunc = [np.mean, np.median, lambda x: np.percentile(x, 80), lambda x: np.percentile(x, 20)]).reset_index()
views_by_days.columns = ['Days Published', 'Mean Views', 'Median Views', '80 Percentile Views', '20 Percentile Views']
views_by_days = views_by_days[views_by_days['Days Published'].between(0,45)]

cumulative_views = views_by_days.loc[:,['Days Published', 'Median Views', '80 Percentile Views', '20 Percentile Views']]
cumulative_views.loc[:, ['Median Views', '80 Percentile Views', '20 Percentile Views']] = cumulative_views.loc[:, ['Median Views', '80 Percentile Views', '20 Percentile Views']].cumsum()

temp_com_all = pd.merge(com_all.loc[:,['Date', "VidId"]], met_vid.loc[:,['Video', 'Video Title']], left_on = 'VidId', right_on = 'Video')
temp_com_all['Date'] = temp_com_all['Date'].apply(lambda x: x.date())
temp_com_all['No of Comments'] = 1

comments_by_date = pd.pivot_table(temp_com_all, index = ['VidId', 'Video Title','Date'], aggfunc ={'No of Comments' : np.sum} ).reset_index()


# ## Dashboard

def main():
    
    st.title("Youtube Channel Data Analysis")
    
    dropbox_items = ('Aggregate Metrics','Aggregated Tabular Metrics', 'Individual Video Analysis')
    sidebar = st.sidebar.selectbox('Menu', dropbox_items)

    if sidebar == dropbox_items[0]:
        st.subheader(dropbox_items[0])
        metrics = met_vid[['Video Publish Time', 'Views', 'Likes', 'Dislikes', 'Shares', 'Comments Added', 'Subscribers', 'Subscribers Lost', 'Subscribers Gained', 'Impressions', 'Impressions Click-through Rate(%)', 'Average Percentage Viewed(%)', 'Average View Duration(sec)', 'RPM(USD)', 'CPM(USD)', 'Your Estimated Revenue(USD)']]
        offset_6month = metrics['Video Publish Time'].max() - pd.DateOffset(months = 6)
        metric_median_6month = metrics[metrics['Video Publish Time'] >= offset_6month].median()
        metric_median_all = metrics[metrics.columns[:]].median()

        col1, col2, col3, col4, col5 = st.columns(5)
        columns = [col1, col2, col3, col4, col5]

        count = 0
        for i in metric_median_6month.index[1:]:
            with columns[count]:
                delta = (metric_median_6month[i] - metric_median_all[i])/metric_median_all[i]
                st.metric(label = i, value = round(metric_median_6month[i], 1), delta = "{:.2%}".format(delta))
                count += 1
                if count >= 5:
                    count = 0

    if sidebar == dropbox_items[1]:
        st.subheader(dropbox_items[1])
        columns = ['Video Title', 'Video Publish Time', 'Views', 'Likes', 'Comments Added', 'Shares', 'Subscribers Gained', 'Subscribers Lost', 'Average View Duration', 'Your Estimated Revenue(USD)', 'Impressions Click-through Rate(%)']
        temp_vid_final = temp_vid[columns]

        numeric_cols = temp_vid_final.columns[np.array((temp_vid_final.dtypes == 'float64') | (temp_vid_final.dtypes == 'int64'))]
        col_format = {}
        for i in numeric_cols:
            col_format[i] = '{:.1%}'.format

        st.dataframe(temp_vid_final.style.applymap(color).format(col_format))

    if sidebar == dropbox_items[2]:
        st.subheader(dropbox_items[2])
        dropbox_items_2 = tuple(met_vid['Video Title'])
        video_dropbox = st.selectbox('Published Video', dropbox_items_2)

        
        selected_video_extra = met_con_sub[met_con_sub['Video Title'] == video_dropbox]
        selected_video_extra.sort_values('Is Subscribed', inplace = True)

        fig_1 = pl.bar(selected_video_extra, x='Is Subscribed', y = 'Views', color = 'Country Code', orientation = 'v')
        
        fig_1.update_layout(title = 'Views Statistics')
        
        st.plotly_chart(fig_1)

        selected_video_extra_2 = temp_vid_per[temp_vid_per['Video Title'] == video_dropbox]
        first_45 = selected_video_extra_2[selected_video_extra_2['Days Published'].between(0,45)]
        first_45.sort_values('Days Published', inplace = True)

        fig_2 = go.Figure()
        fig_2.add_trace(go.Scatter(x = cumulative_views['Days Published'], y = cumulative_views['20 Percentile Views'], mode = 'lines', name = '20 Percentile Views', line = dict(color = '#26D9C7', dash = 'dash')))
        fig_2.add_trace(go.Scatter(x = cumulative_views['Days Published'], y = cumulative_views['Median Views'], mode = 'lines', name = '50 Percentile Views', line = dict(color = '#91D926', dash = 'dash')))
        fig_2.add_trace(go.Scatter(x = cumulative_views['Days Published'], y = cumulative_views['80 Percentile Views'], mode = 'lines', name = '80 Percentile Views', line = dict(color = '#D92638', dash = 'dash')))
        fig_2.add_trace(go.Scatter(x = first_45['Days Published'], y = first_45['Views'].cumsum(), mode = 'lines', name = "Current Video", line = dict(color = '#6E26D9')))

        fig_2.update_layout(title = "First 45 Days Comparison", xaxis_title = 'Days Since Published', yaxis_title = 'Cumulative Views')

        st.plotly_chart(fig_2)
        
        selected_video_extra_3 = comments_by_date[comments_by_date['Video Title'] == video_dropbox]
        fig_3 = go.Figure()
        fig_3.add_trace(go.Scatter(x = selected_video_extra_3['Date'], y = selected_video_extra_3['No of Comments'], name = 'No of Comments', line = dict(color = 'Firebrick')))
        
        fig_3.update_layout(title = 'User Comments', xaxis_title = "Date", yaxis_title = 'No of Comments')

        st.plotly_chart(fig_3)        

if __name__ == '__main__':
    main()
