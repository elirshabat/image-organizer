from argparse import ArgumentParser
import os
import yaml
from utils import list_subtree, is_image
import face_recognition


def _main():
    seed_dir = args.seed_dir
    faces_file = os.path.join(seed_dir, "faces.yml")

    with open(faces_file, 'rt') as f:
        faces_dict = yaml.load(f, Loader=yaml.FullLoader)

    img_dir = args.img_dir
    all_files = list_subtree(img_dir, recursive=args.recursive)
    img_files = [f for f in all_files if is_image(f)]

    face_names, face_encodings = [], []
    for name, face_file in faces_dict.items():
        face_image = face_recognition.load_image_file(face_file)
        enc = face_recognition.face_encodings(face_image)[0]
        face_names.append(name)
        face_encodings.append(enc)

    for img_f in img_files:
        curr_image = face_recognition.load_image_file(img_f)
        curr_encodings = face_recognition.face_encodings(curr_image)
        comparison_results = face_recognition.compare_faces(curr_encodings, face_encodings)
        print(comparison_results)


if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument("seed_dir", help="The seed directory must contain images of all the faces need to be tagged"
                                             " as well as 'faces.yml' file that maps names to images in the folder")
    arg_parser.add_argument("img_dir", help="Root folder for images to tag")
    arg_parser.add_argument("--recursive", "-r", action="store_true",
                            help="indicate to apply recursively on source directory")
    arg_parser.add_argument("--out_file", "-o", required=True,
                            help="Path to output file that maps files to list of tags")
    args = arg_parser.parse_args()

    _main()
