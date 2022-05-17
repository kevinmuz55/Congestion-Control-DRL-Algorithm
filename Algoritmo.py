from gym import Env
from main import *
import math
from gym.spaces import Discrete, Box #Espacio discreto y espacio caja
import numpy as np
import random
import sys
import matplotlib.pyplot as plt

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten, Dropout
from tensorflow.keras.optimizers import Adam

from rl.agents import DQNAgent
from rl.policy import BoltzmannQPolicy
from rl.memory import SequentialMemory

import itertools
import subprocess

Res_cpu = 100 #x10^-2
Res_me = 4000000000
eta = -1 #η
theta = 1 #θ
#nu_cpu = 0.2 #v
nu_cpu = 5 #v
NumCoresD1=4
NumCoresD2=1


estados = [[],[],[],[]]
pasos = 100
pasosList = list(range(0, pasos))
train_steps = 100000
action_space_size = 21

# Define el entorno
class NetworkEnv(Env):
    def __init__(self):
        # Acciones disponibles; subir, bajar, mantener
        self.action_space = Discrete(action_space_size)
        # Arreglo porcentaje de recursos asignados y usados
        self.observation_space = Box(low=0, high=Res_cpu, shape=(1,5))
        # Establece los recursos asignados y usados
        self.state = [0,0,0,0,0]
        # Duracion
        self.length = pasos
        self.numCoresD1=NumCoresD1
        self.numCoresD2=NumCoresD2
        self.latency=[]
        self.repeticiones=0
        self.NumRepeats = 3

    def step(self, action):
        # Modifica la accion a tomar en positivo y negativo
        take_action = action - 10
        # Aplica la acción
        self.state[0] += take_action
        #Aplica random al state [2]
        """ self.state[2] += random.randint(-10,10)
        if(self.state[2]<=0):
            self.state[2] = 1  """
        # Reduce la duracion en 1
        self.length -= 1

        # Calcula la recompensa
        if(self.state[0] >= Res_cpu or self.state[0] <= 0):
            reward = eta*100
        elif (self.state[0] >= self.state[2] + nu_cpu):
            # Agrega violación
            self.state[4] += 0.001
            #reward = theta*np.exp(self.state[4])
            reward = theta*((self.state[2] + nu_cpu)/self.state[0])
            #reward = theta
        else:
            # Reinicia violación
            self.state[4] = 0.0
            #reward = eta*(self.state[2]/self.state[0])
            #reward = eta*np.exp(self.state[4])
            reward = eta*10

        """ # Fallo total CPU
        if self.state[0] >= Res_cpu or self.state[0] <= 0:
            done = True """

        # Duracion completada
        if sys.argv[1] == "Start":
            if self.length <= 0:
                self.numCoresD2 = int(math.ceil(self.state[0]/10))
                test(states,actions)
                self.repeticiones+=1
                if(self.repeticiones == self.NumRepeats):
                    done = True
                else:
                    self.length = pasos
            else:
                done = False
        else:
            if self.length <= 0:
                done = True
            else:
                done = False

        

        # Aplica ruido
        #self.state += random.randint(-1,1)

        # Establece un marcador de posicion para la informacion
        info = {}

        # Retorna la informacion del step
        return self.state, reward, done, info

    def render(self, mode="human"):
        estados[0].append(self.state[0])
        estados[1].append(self.state[1])
        estados[2].append(self.state[2])
        estados[3].append(self.state[3])

        if len(estados[0])==pasos:
            ypoints_ar_cpu = np.array(estados[0])
            ypoints_ar_me = np.array(estados[1])
            ypoints_ur_cpu = np.array(estados[2])
            print(ypoints_ur_cpu)
            ypoints_ur_me = np.array(estados[3])
            xpoints = np.array(pasosList)
            plt.xlabel("Pasos")
            plt.ylabel("Unidades de CPU")
            #plt.plot(xpoints, ypoints_ar_me, color ='orange', label ='C CPU (Asignados)')
            #plt.plot(xpoints, ypoints_ur_me, color ='g', label ='U CPU (Usados)')
            plt.plot(xpoints, ypoints_ar_cpu, color ='r', label ='Recursos Asignados')
            plt.plot(xpoints, ypoints_ur_cpu, color ='b', label ='Recursos Usados')
            plt.legend()
            plt.grid()
            plt.show()
            estados[0].clear()
            estados[1].clear()
            estados[2].clear()
            estados[3].clear()
        return

    def reset(self):
        # Reinicia recursos asignados
        self.state = get_initial_state(self)
        #self.state = [random.randint(0, 100),0,50,0,0]

        # Reinicia la duracion
        self.length = pasos

        return self.state

def get_initial_state(self):
    if sys.argv[1] == "Start":
        StartTopology()
        UpdateCPU(self.numCoresD1,self.numCoresD2)
        AddSurgery(3)
        time.sleep(5)
        ur_cpu=obtainCPUMEM(self.numCoresD1,self.numCoresD2)[1]
        ur_me=obtainCPUMEM(self.numCoresD1,self.numCoresD2)[2]
        time.sleep(25)
        self.latency.append(ObtainLatency())
        np.savetxt('latency.csv',self.latency,delimiter=',')
        ShutDown()
        ar_cpu = self.numCoresD2*10
        ar_me = 100

    else :
        ur_cpu = random.randint(0,100)
        ur_me = random.randint(0,100)
        latency = random.randint(15,120)
        #ar_me = random.randint(0, Res_me)
        #ur_cpu = random.randint(0, ar_cpu)
        #ur_me = random.randint(0, ar_me)

        ar_cpu = random.randint(0,100)
        ar_me = random.randint(0,100)

        #C_cpu = data.ar_cpu / Res_cpu
        #C_me = data.ar_me / Res_me
        #U_cpu = data.ur_cpu / data.ar_cpu
        #U_me = data.ur_me / data.ar_me
        #I_cpu = data.ur_cpu / data.ar_cpu
        #I_me = data.ur_me / data.ar_me

    Violation = 0

    return [ar_cpu, ar_me, ur_cpu, ur_me, Violation]

def train(states, actions):
    model = get_model(states, actions)
    model.summary()
    dqn = get_agent(model, actions)
    dqn.compile(Adam(learning_rate=1e-3), metrics=['mae'])
    dqn.fit(env, nb_steps=train_steps, visualize=False, verbose=1)
    dqn.save_weights('dqn_weights.h5f', overwrite=True)

def test(states, actions):
    model = get_model(states, actions)
    dqn = get_agent(model, actions)
    dqn.compile(Adam(learning_rate=1e-3), metrics=['mae'])
    dqn.load_weights('dqn_weights.h5f')
    if sys.argv[1] == "Start":
        dqn.test(env, nb_episodes=1, visualize=True)
    else:
        dqn.test(env, nb_episodes=10, visualize=True)

def get_model(states, actions):
    # Crea la red neuronal
    model = Sequential()

    # Aplanar unidades
    model.add(Flatten(input_shape=(states)))

    # Add a hidden layers with dropout
    model.add(Dense(24, activation="relu", input_shape=states))
    model.add(Dense(24, activation="relu"))
    #model.add(Dropout(0.5))

    # Add an output layer with output units
    model.add(Dense(actions, activation="linear"))

    return model

def get_agent(model, actions):
    #Construye una ley de probabilidad sobre los valores de q y devuelve
    # una acción seleccionada al azar de acuerdo con esta ley.
    policy = BoltzmannQPolicy()

    #Proporciona una estructura de datos rápida y eficiente en la que podemos
    # almacenar las experiencias del agente.
    memory = SequentialMemory(limit=50000, window_length=1)

    #Crea el agente
    #nb_steps_warmup: Se utilizan para reducir la tasa de aprendizaje con el
    # fin de reducir el impacto de desviar el modelo del aprendizaje en la
    # exposición repentina a nuevos conjuntos de datos.
    #target_model_update: reemplaza la red con una copia nueva sin entrenar
    # de vez en cuando
    #enable_double_dqn: Habilita la doble dqn
    dqn = DQNAgent(model=model, memory=memory, policy=policy, nb_actions=actions, nb_steps_warmup=10, target_model_update=1e-2, enable_double_dqn=True)

    return dqn

if __name__ == "__main__":
    latency=[]


    if len(sys.argv) != 2:
        print("Es necesario colocar un argumento:")
        print("Entrenamiento: Train, Ensayos: Test, Ejecutar: Start")
    else:
        env = NetworkEnv()
        env.reset()
        states = env.observation_space.shape
        actions = env.action_space.n
        if sys.argv[1] == "Train":
            train(states, actions)
        elif sys.argv[1] == "Test":
            test(states, actions)
        elif sys.argv[1] == "Start":
            test(states, actions)
        else:
            print("Argumento "+sys.argv[1]+" no es válido.")
            print("Entrenamiento: Train, Ensayos: Test, Ejecutar: Start")
        #state_space()