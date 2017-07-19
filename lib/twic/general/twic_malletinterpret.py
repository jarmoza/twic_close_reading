import glob
import json
import time
import os
import sys

def load_src(name, fpath):
    import os, imp
    return imp.load_source(name, os.path.join(os.path.dirname(__file__), fpath))

load_src("utils_jensen_shannon", os.path.join("..", "utils", "utils_jensen_shannon.py"))
import utils_jensen_shannon

load_src("utils_color", os.path.join("..", "utils", "utils_color.py"))
from utils_color import Utils_Color

from twic_malletscript import TWiC_MalletScript
from twic_text import TWiC_Text

load_src("utils_malletinterpret", os.path.join("..", "utils", "utils_malletinterpret.py"))
from utils_malletinterpret import Utils_MalletInterpret
clean_word = Utils_MalletInterpret.CleanWord


class TWiC_MalletInterpret:

    @staticmethod
    def Build_TextObjects(TextClass, mallet_script, tp_collection):

        return [TextClass(tp.filename) for tp in tp_collection]


    @staticmethod
    def Build_WordTopicFileIndices(filename, current_fwt):

        input_file = open(filename, "rU")
        data = input_file.readlines()
        input_file.close()

        statefile_word_index = 0

        # This function builds two lists:
        #    (1) List of indices that map a word's index in the given file to its topic number (or none)
        #    (2) List of indices that map a word's index in a line in the given file to its topic number (or none)

        # Maps number index to its topic or non-topic
        # Commented out 7/9/17 as it is unused by TWiC Close Reading, J. Armoza
        # file_wordtopic_map = []

        # Maps number index to lines, each of which contain another list/map of word-by-index to topic number
        line_wordtopic_map = []

        # Building an array of arrays (each of which have two entries: a string and map of word index to topic ids)
        for line in data:

            words = line.strip().split(" ")
            words[:] = [word for word in words if len(word) > 0]

            # Add an entry to the line map
            line_wordtopic_map.append([line.strip().split(" "), []])

            if statefile_word_index < len(current_fwt.word_info):
                lowercase_state_word = clean_word(current_fwt.word_info[statefile_word_index].word.lower())

            # Go through each word in the line
            for actual_word_index in range(len(words)):

                # Lowercase only for comparison
                lowercase_word = clean_word(words[actual_word_index].lower())

                # If this word from the file matches the current statefile word
                if statefile_word_index < len(current_fwt.word_info) and (lowercase_word == lowercase_state_word):
                   # NOTE: Extra condition was for workaround for MALLET regex/punctuation issue with import-dir
                   # or ("\'" in words[actual_word_index].lower() and lowercase_word != lowercase_state_word)):

                    statefile_word_index += 1

                    if statefile_word_index < len(current_fwt.word_info):

                        lowercase_state_word = clean_word(current_fwt.word_info[statefile_word_index].word.lower())

                    # Add an entry for the matched word in the file and line maps for this topic
                    line_wordtopic_map[len(line_wordtopic_map) - 1][1].append(current_fwt.word_info[statefile_word_index - 1].topic)
                    # file_wordtopic_map.append(current_fwt.word_info[statefile_word_index - 1].topic)

                else:

                    # Add a blank entry (-1) for this word in the file and line maps for this word
                    line_wordtopic_map[len(line_wordtopic_map) - 1][1].append(-1)
                    # file_wordtopic_map.append(-1)

        # return file_wordtopic_map, line_wordtopic_map
        return line_wordtopic_map


    @staticmethod
    def ConvertTextToJSON(text, json_output_directory, mallet_script, state_file_data=None, write_json=True):

        json_data = { "document" : {} }

        # Store filename
        json_data["document"]["filename"] = text.GetFilename()

        # Store the text's title
        json_data["document"]["title"] = text.GetTitle()

        # Store each line and its associated topic-word info
        json_data["document"]["lines_and_colors"] = []

        # No state file data given
        if None == state_file_data:

            # Write out the data to a JSON file (format as seen in output/viz_input_docformat.json)
            if write_json:
                with open(json_output_directory + text.GetFilename() + ".json", "w") as fileptr:
                    fileptr.write(json.dumps(json_data))
            return None

        # Get topic word indexes for this text
        filepath = mallet_script.corpus_source_dir + text.GetFilename() + ".txt"
        # file_wordtopic_map, line_wordtopic_map = TWiC_MalletInterpret.Build_WordTopicFileIndices(filepath, state_file_data)
        line_wordtopic_map = TWiC_MalletInterpret.Build_WordTopicFileIndices(filepath, state_file_data)

        line_index = 0
        for line in line_wordtopic_map:

            line_entry = [line[0], {}]

            for index in range(len(line_wordtopic_map[line_index][1])):
                if -1 != line_wordtopic_map[line_index][1][index]:
                    line_entry[1][str(index)] = str(line_wordtopic_map[line_index][1][index])

            json_data["document"]["lines_and_colors"].append(line_entry)

            line_index += 1
            # TO BE CONTINUED HERE

        # Write out the data to a JSON file (format as seen in output/viz_input_docformat.json)
        if write_json:
            with open(json_output_directory + text.GetFilename() + ".json", "w") as fileptr:
                fileptr.write(json.dumps(json_data))

        return json_data
