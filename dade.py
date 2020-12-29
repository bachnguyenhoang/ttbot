import discord
import random
import re
from discord.ext import commands
import pandas as pd

class DaDe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # game state
        self.__dade_state = 0 # 0: init, 1: in game
        # game database
        self.__dade_db = None
        # current question
        self.__dade_hints = []
        self.__dade_hints_open = []
        self.__dade_hints_opened = 0
        self.__dade_question = ''
        self.__dade_answer = ''
        self.__dade_attempts = 0
        self.__dade_accepted_answers = []
        
        # user id
        self.__init_user_id = 0
        self.__owner_user_id = 0
        
        self.init_dade_db()
        
    #main command of da de
    @commands.command(help='Start a new `da dê`')
    async def dade(self, ctx, *args):
        if (self.__dade_state == 0):
            if (len(args) >= 1):
                await ctx.channel.send("No `da dê` game is in progress! Try `tt!dade` for a new `da dê` or `tt!help` for more information")
                return

            #reinit hint_opened
            self.__dade_hints_opened = 0
            self.__dade_hints = []
            self.__dade_hints_open = []
            #init attempts
            self.__dade_attempts = 0
            
            # init user id
            self.__init_user_id = ctx.author.id
            #randomly select a question
            #init question from database
            line = self.__dade_db.sample(n=1)
            self.__dade_question, self.__dade_answer = line['Content'].values[0], line['Answer'].values[0]

            #init answer
            self.__dade_accepted_answers = line['Keywords'].values[0]
            #parse hints to array
            hints = re.finditer(r'\[[\w/,\"\s\.\-]*\]', self.__dade_question)

            #modify question to hide the hints. move the hints to a separate array
            counter = 1
            string_shrink = 0
            for hint in hints:
                start_idx = hint.start()
                end_idx = hint.end()
                self.__dade_hints.append(hint[0])
                self.__dade_question = self.__dade_question[0:start_idx- string_shrink] + '[' + str(counter) + ']' + self.__dade_question[end_idx - string_shrink:]
                string_shrink += end_idx - start_idx - 3
                counter += 1

            #init hints open
            self.__dade_hints_open = [0 for _ in range(len(self.__dade_hints))]
            await ctx.channel.send(self.__dade_question)

            self.__dade_state = 1
            return
        elif (self.__dade_state == 1):
            if (len(args) < 1):
                await ctx.channel.send("a `da dê` game is in progress!\nType `tt!dade hint` for hints\nType `tt!dade ans 'your answer'` to answer\nType `tt!dade quit` to quit and see the answer")
                return
            if (args[0] == 'hint'):
                hint_loc_stm = self.open_hint()
                if (hint_loc_stm == 0):
                    await ctx.channel.send("No hint left!\n" + self.__dade_question)
                else:
                    re_pattern = r'\[' + str(hint_loc_stm) + r'\]'
                    result = re.search(re_pattern, self.__dade_question)
                    
                    self.__dade_question = self.__dade_question[:result.start()] + self.__dade_hints[hint_loc_stm-1] + self.__dade_question[result.end():]
                    await ctx.channel.send('Hint ' + str(hint_loc_stm) + ' opened!\n' + self.__dade_question)
                return
            if (args[0] == 'quit'):
                if (ctx.author.id == self.__init_user_id) or (ctx.author.id == self.__owner_user_id):
                    while (True):
                        hint_loc_stm = self.open_hint()
                        if (hint_loc_stm == 0):
                            break
                        re_pattern = r'\[' + str(hint_loc_stm) + r'\]'
                        result = re.search(re_pattern, self.__dade_question)

                        self.__dade_question = self.__dade_question[:result.start()] + self.__dade_hints[hint_loc_stm-1] + self.__dade_question[result.end():]

                    await ctx.channel.send('Full question:\n> ' + self.__dade_question + "\nAnswer:`" + self.__dade_answer + "`")

                    self.__dade_state = 0
                else:
                    answers_msg = "Only <@" + str(self.__owner_user_id) + ">"

                    if self.__owner_user_id != self.__init_user_id:
                        answers_msg += " or <@" + str(self.__init_user_id) + ">"
                    answers_msg += " can quit the game!"
                    await ctx.channel.send(answers_msg)

                return
            if (args[0] == 'ans'):
                ans = ' '.join(args[1:])

                if ans.lower() in self.__dade_accepted_answers:
                    self.__dade_attempts += 1
                    hints_used = self.__dade_hints_opened
                    while (True):
                        hint_loc_stm = self.open_hint()
                        if (hint_loc_stm == 0):
                            break
                        re_pattern = r'\[' + str(hint_loc_stm) + r'\]'
                        result = re.search(re_pattern, self.__dade_question)

                        self.__dade_question = self.__dade_question[:result.start()] + self.__dade_hints[hint_loc_stm-1] + self.__dade_question[result.end():]

                    await ctx.channel.send('Congrats ' + ctx.author.mention + '! You used ' + str(hints_used) + ' hint(s)\nYou solved this `da dê` in ' + str(self.__dade_attempts) + ' attempt(s)' + '\n\nFull question:\n> ' + self.__dade_question+'\n\n'+"Answer:`" + self.__dade_answer + "`")
                    self.__dade_state = 0
                else:
                    self.__dade_attempts += 1
                    print("[DEBUG] received: " + ans.lower())
                    print("[DEBUG] expect: " + str(self.__dade_accepted_answers))
                    await ctx.channel.send("Incorrect! Please try again")
                return

            #default: if command not recognized, send help message
            await ctx.channel.send("Command not recognized!\nType `tt!dade hint` for hints\nType `tt!dade ans 'your answer'` to answer\nType `tt!dade quit` to quit and see the answer")
            return

    #randomly open a hint
    def open_hint(self):
        max_num_of_hints = len(self.__dade_hints_open)
        if (self.__dade_hints_opened == max_num_of_hints):
            return 0

        while (True):
            hint_loc = random.randint(0, max_num_of_hints - 1)
            if (self.__dade_hints_open[hint_loc] == 1):
                continue
            else:
                self.__dade_hints_open[hint_loc] = 1
                self.__dade_hints_opened += 1
                return hint_loc + 1

    #init database from csv file
    def init_dade_db(self):
        df = pd.read_csv('database/dade.tsv', delimiter='\t')
        df.drop(['STT','Author'], axis=1, inplace=True)

        dade_db = []

        for i, row in df.iterrows():
            line = [row['Content'], row['Answer'], row['Keywords'].lower().split(',')]
            dade_db.append(line)

        self.__dade_db = pd.DataFrame(dade_db, columns=['Content', 'Answer','Keywords'])

        return
    
