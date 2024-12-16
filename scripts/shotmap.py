import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
from mplsoccer import VerticalPitch
import understatapi
import argparse
import sys
sys.path.insert(1,'../fonts/')

client = understatapi.UnderstatClient()


def get_players(player,league='EPL',season='2024'):
    """
    Get Players from selected league.

    player: Full player name (working on specifics e.g: letters with accents, first/last names only etc.)
    league: Default is Premier League
    season: Season they were playing in the league (default 2024-25 season). ##This doesn't really matter except for those who were
    """

    ## DATAFRAME OF ALL PLAYERS THAT WERE IN SPECIFIED LEAGUE IN SPECIFIED SEASON
    all_players = pd.DataFrame(client.league(league=league).get_player_data(season=season))

    return all_players[all_players.player_name == player]['id'].values[0]
    

def load_font():
    font_path = 'fonts/Arvo/Arvo-Regular.ttf'
    font_props = font_manager.FontProperties(fname=font_path)
    return font_props

def get_shot_data(player_id):
    "Gets all shot data for the player across all seasons."
    shot_data = client.player(player=str(player_id)).get_shot_data()
    return pd.DataFrame(shot_data)

def create_shotmap(df, player_name, season,background_color='#0C0D0E', figsize=(8,12)):
    """
    Create a shot map visualization for a player
    
    Parameters:
        df: DataFrame containing shot data
        player_name: Name of the player for the title
        background_color: Color for background (default '#0C0D0E')
        figsize: Size of figure (default (8,12))
    """
    
    ### GET STATISTICS FOR SHOT DATA
    df = df[df.season == season]
    df['X'] = pd.to_numeric(df['X']) * 100  
    df['Y'] = pd.to_numeric(df['Y']) * 100
    df['xG'] = pd.to_numeric(df['xG'])
    tot_shots = df.shape[0]
    tot_goals = df[df.result == 'Goal'].shape[0]
    tot_xg = df.xG.astype(float).sum()
    xg_per_shot = tot_xg/tot_shots
    df.X = df.X.astype(float)
    points_avg_distance = df.X.mean()

    actual_avg_distance = 120 - (df.X.values * 1.2).mean()

    
    ### CREATE FIGURE
    fig = plt.figure(figsize=figsize)
    fig.patch.set_facecolor(background_color)
    font_props = load_font()
    
    ### ax1, THE TOP TEXTS
    year = int(season)
    season_text = f'All shots in {year} - {year + 1}'
    
    ax1 = fig.add_axes([0, 0.7, 1, .2])
    ax1.set_facecolor(background_color)
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    
    ax1.text(x=0.5, y=.85, s=player_name, fontsize=20, color='white', ha='center',fontproperties=font_props)
    ax1.text(x=0.5, y=.7, s=f'{season_text}', fontsize=14, color='white', ha='center',fontproperties=font_props)
    ax1.text(x=0.25, y=.5, s='Low quality chance', fontsize=12, color='white', ha='center',fontproperties=font_props)
    ax1.text(x=0.75, y=.5, s='High quality chance', fontsize=12, color='white', ha='center',fontproperties=font_props)

    circles = [(0.37, 100), (0.42, 200), (0.48, 300), (0.54, 400), (0.6, 500)]
    for x, s in circles:
        ax1.scatter(x, 0.53, s=s, color=background_color, edgecolor='white', linewidth=.8)

    ax1.text(x=.45, y=.27, s='Goal', fontsize=10, color='white', ha='right',fontproperties=font_props)
    ax1.scatter(0.47, 0.3, s=100, color='red', edgecolor='white', linewidth=.8, alpha=0.7)
    ax1.text(x=.55, y=.27, s='No Goal', fontsize=10, color='white', ha='left',fontproperties=font_props)
    ax1.scatter(0.53, 0.3, s=100, color=background_color, edgecolor='white', linewidth=.8)

    ax1.set_axis_off()

    ### ax2, THE PITCH AND SHOTS
    ax2 = fig.add_axes([.05, 0.25, .9, .5])
    ax2.set_facecolor(background_color)

    pitch = VerticalPitch(pitch_type='opta', half=True, pitch_color=background_color, 
                         pad_bottom=0.5, line_color='white', linewidth=0.75, axis=False, label=False)
    pitch.draw(ax=ax2)

    #### PLOT SHOTS
    for i in df.to_dict(orient='records'):
        pitch.scatter(float(i['X']), float(i['Y']), s=300*float(i['xG']), 
                     color='red' if i['result'] == 'Goal' else background_color,
                     ax=ax2, alpha=0.7, linewidth=0.8, edgecolor='white')

    ### ax3, THE ATHLETIC STYLE VISUALISATIONS
    ax3 = fig.add_axes([0., 0.2, 1, 0.05])
    ax3.set_facecolor(background_color)

    stats = [
        ('Shots', tot_shots, 0.25),
        ('Goals', tot_goals, 0.38),
        ('xG', f'{tot_xg:.2f}', 0.53),
        ('xG/Shot', f'{xg_per_shot:.2f}', 0.64)
    ]

    for label, value, x_pos in stats:
        ax3.text(x=x_pos, y=.5, s=label, fontsize=20, color='white', ha='left',fontproperties=font_props)
        ax3.text(x=x_pos, y=0, s=str(value), fontsize=16, color='red', ha='left',fontproperties=font_props)

    ax3.set_axis_off()
    return fig



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Create a "The Athletic" style shot map for a player.')
    
    parser.add_argument('player', type=str, help='Full name of the player e.g: Bukayo Saka, Erling Haaland.')
    parser.add_argument('--season', type=str, default='2024', 
                        help='Season to analyse (default: 2024)')
    parser.add_argument('--league', type=str, default='EPL',
                        help='League name (default: EPL). Other options are Serie A, La Liga, Ligue 1.')
    parser.add_argument('--save',action='store_true')
    
    
    args = parser.parse_args()



    
    pid = get_players(args.player)
    df = get_shot_data(pid)

    seasons = sorted(df['season'].unique()) if args.season.lower() == 'all' else [args.season]
    
    for season in seasons:
        fig = create_shotmap(df, args.player, season=season)
        if args.save:
            fig.savefig(f'shotmap_{args.player.replace(" ", "")}_{int(args.season)}_{int(args.season) + 1}.png',dpi=300)
        plt.draw()
        plt.pause(0.1)
    plt.show()
