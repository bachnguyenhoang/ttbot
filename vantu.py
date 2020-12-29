import discord
import random
import re
from discord.ext import commands
import pandas as pd
from typing import Dict, List

class VanTu(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
        self.__vantu_state = 0
        self.__questions_db : pd.DataFrame = None
        self.__current_topic = ''
        self.__current_answers : List = list()
        self.__encoded_answers : List = list()
        self.__answer_status : List = list()

        # keep track of user ids that can quit
        self.__init_user_id = 0
        self.__owner_user_id = 0

        self.initialize_vtc_questions()

    @commands.command(help='Start a new `văn tự cổ`')
    async def vantu(self, ctx, *args):
        
        if (self.__vantu_state == 0):

            if (len(args) > 0):
                await ctx.channel.send("type `tt!vantu` to start a new game!")
                return
            # init questions & answers
            self.__current_answers = []
            self.__encoded_answers = []
            self.__answer_status = []
            question = self.__questions_db.sample(n=1)
            self.__current_topic, answers = question.index[0], question.values[0]
            
            #init start user id (for quit command)
            self.__init_user_id = ctx.author.id

            answers_msg : str = "A new `văn tự cổ` started by " + ctx.author.mention + '\n\n'
            answers_msg += "Chủ đề: `" + self.__current_topic + '`\n'
            print("[DEBUG] topic: " + str(self.__current_topic))
            
            for i, answer in enumerate(answers):
                if answer is None:
                    break

                self.__current_answers.append(answer)
                self.__answer_status.append(0)
                def strip_vowels(answer):
                    return ''.join(re.findall(r'[QWRTYÝỶỸỴỲPSDĐFGHJKLZXCVBNM,/\(\)\[\]\{\}\'\"\s0-9\-\.\?]+',answer)).replace(' ','')

                def randomly_insert_whitespaces(answer):
                    ret : str = ''
                    for letter in answer:
                        if random.randint(0,1) == 0:
                            ret += letter
                            ret += ' '
                        else:
                            ret += letter
                    return ret

                encoded_question = strip_vowels(answer)
                self.__encoded_answers.append(randomly_insert_whitespaces(encoded_question))
                
                answers_msg += '#{}: {}'.format(i+1, self.__encoded_answers[i]) + '\n'

            print("[DEBUG] topic answers: " + str(self.__current_answers))
            answers_msg += "\nType `tt!vantu ans 'no. of keyword' 'your answer'` to answer!\ne.g `tt!vantu ans 1 HUI SUX`"
            await ctx.channel.send(answers_msg)
            
            self.__vantu_state = 1
            return
        if (self.__vantu_state == 1):
            if len(args) < 1:
                answers_msg = "Another game is in progress!\nType `tt!vantu ans 'no. of keyword' 'your answer'` to answer!\ne.g `tt!vantu ans 1 HUI SUX`\n"
                answers_msg += "Chủ đề: `" + self.__current_topic + '`\n'
                for i, val in enumerate(self.__answer_status):
                    if (val == 1):
                        answers_msg += '#{}: {}'.format(i+1, self.__current_answers[i]) + '\n'
                    else:
                        answers_msg += '#{}: {}'.format(i+1, self.__encoded_answers[i]) + '\n'
                await ctx.channel.send(answers_msg)
                return
                
            if (args[0] == 'ans'):
                ans_index = 0

                try:
                    ans_index = int(args[1])
                except ValueError:
                    await ctx.channel.send("Invalid parameters! Please use a number in range {}-{}.".format(1,len(self.__answer_status)))
                    return

                try:
                    print("[DEBUG] expect: " + str(self.__current_answers[ans_index - 1]))
                    print("[DEBUG] received: " + str(' '.join(args[2:])))
                    result = ' '.join(args[2:]).lower() == self.__current_answers[ans_index - 1].lower()
                except IndexError:
                    await ctx.channel.send("Invalid parameters! Please use a number in range {}-{}.".format(1,len(self.__answer_status)))
                    return

                if result is True and (self.__answer_status[ans_index - 1] != 1):
                    self.__answer_status[ans_index - 1] = 1

                    answers_msg = "Congrats {}, you solved `văn tự` {}!\n\n".format(ctx.author.mention,ans_index)

                    answers_msg += "Chủ đề: `" + self.__current_topic + '`\n'
                    for i, val in enumerate(self.__answer_status):
                        if (val == 1):
                            answers_msg += '#{}: {}'.format(i+1, self.__current_answers[i]) + '\n'
                        else:
                            answers_msg += '#{}: {}'.format(i+1, self.__encoded_answers[i]) + '\n'
                    await ctx.channel.send(answers_msg)
                elif self.__answer_status[ans_index - 1] == 1:
                    answers_msg = "You're too late {}, `văn tự` {} already solved!\n\n".format(ctx.author.mention,ans_index)
                    await ctx.channel.send(answers_msg)
                else:
                    await ctx.channel.send("Answer for `văn tự` {} is incorrect! {} please try again!".format(ans_index, ctx.author.mention))
                    return
                    
                if 0 not in self.__answer_status:
                    self.__vantu_state = 0
                    await ctx.channel.send("Congratulation! all `văn tự` were solved!")
            elif (args[0] == 'quit'):
                if (ctx.author.id == self.__init_user_id) or (ctx.author.id == self.__owner_user_id):
                    answers_msg = ctx.author.mention + " quitted the game.\n"
                    answers_msg += "Chủ đề: `" + self.__current_topic + '`\n'
                    for i, val in enumerate(self.__current_answers):
                        answers_msg += '#{}: {}'.format(i+1, val) + '\n'
                    await ctx.channel.send(answers_msg)
                    self.__vantu_state = 0
                else:
                    answers_msg = "Only <@" + str(self.__owner_user_id) + ">"
                    
                    if self.__owner_user_id != self.__init_user_id:
                        answers_msg += " or <@" + str(self.__init_user_id) + ">"
                    answers_msg += " can quit the game!"
                    await ctx.channel.send(answers_msg)

                return
            else:
                await ctx.channel.send("Command not recognized!\nType `tt!vantu ans 'no. of keyword' 'your answer'` to answer!\ne.g `tt!vantu ans 1 HUI SUX`")
                return

    def initialize_vtc_questions(self, question_file='database/vtc.csv'):
        df = pd.read_csv(question_file)
        df.drop(['Bình luận', 'Unnamed: 5'], axis=1, inplace=True)

        questions_dict: Dict[str, List] = dict()
        previous_id, previous_topic = None, None
        for i, row in df.iterrows():
            if pd.isnull(row['STT']) or pd.isnull(row['Chủ đề']):
                current_id, current_topic = previous_id, previous_topic
            else:
                current_id, current_topic = row['STT'], row['Chủ đề']

            questions_dict.setdefault(current_topic, [])
            if not pd.isnull(row['Đáp án']):
                questions_dict[current_topic].append(row['Đáp án'])

            previous_id, previous_topic = current_id, current_topic
            
        self.__questions_db = pd.DataFrame.from_dict(data=questions_dict,orient='index')

